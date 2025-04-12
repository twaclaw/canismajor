import argparse
import asyncio
import logging
import os
from enum import StrEnum
from typing import Any

import aioconsole
from yaml import safe_load

from hid import QRCodeReader
from stellarium import ScriptType, Stellarium, constellations

logger = logging.getLogger("canismajor")

try:
    from systemd import journal

    logger.propagate = False
    logger.addHandler(journal.JournaldLogHandler())
except ImportError:
    ...


class Behavior(StrEnum):
    """
    Defines what to do with a running script when a  new object arrives in the queue.
    """

    STOP = "stop"
    IGNORE = "ignore"
    WAIT = "wait"


class NamesValidator:
    """
    Validates the objects names before passing them to Stellarium
    """

    def __init__(self, conf: dict[str, Any], stellarium_scripts_path: str):
        self.language = conf["stellarium"]["constellations_language"]
        assert self.language in ["english", "native"]
        self.objects = conf["search"]["objects"]
        self.stellarium_scripts_path = stellarium_scripts_path
        self.standalone_scripts = [
            k for k in conf["scripts"].keys() if k not in ["constellation", "object"]
        ]

    def validate(self, obj) -> tuple[str, ScriptType] | None:
        """
        Introspects the kind of script to run based on the object name.
        """
        obj_title = obj.title()
        if obj_title in self.objects:
            return obj_title, ScriptType.PARAMS_SCRIPT_OBJECTS
        if obj in self.standalone_scripts:
            return obj, ScriptType.STANDALONE_SCRIPT
        if obj_title in constellations.keys():
            if self.language == "english":
                return constellations[
                    obj_title
                ], ScriptType.PARAMS_SCRIPT_CONSTELLATIONS
            return obj_title, ScriptType.PARAMS_SCRIPT_CONSTELLATIONS
        if obj in os.listdir(self.stellarium_scripts_path):
            return obj, ScriptType.STELLARIUM_SCRIPT
        return None


validator: NamesValidator | None = None


async def run_stellarium_script(
    queue: asyncio.Queue, client: Stellarium, behavior: Behavior, timeout: float
):
    global validator
    assert validator
    while True:
        obj = await queue.get()
        logger.debug(f"Received object in queue: {obj}")
        res = validator.validate(obj)
        if res:
            obj, typ = res
            logger.debug(f"Object '{obj}' found in configuration. Type: {typ}")
            if behavior == Behavior.STOP:
                await client.stop_script()
            elif behavior == Behavior.WAIT:
                try:
                    await asyncio.wait_for(
                        client.wait_script_completion(), timeout=timeout
                    )
                except asyncio.TimeoutError:
                    await client.stop_script()

            if not await client.is_script_running():
                await client.focus(obj, typ)
            queue.task_done()
        else:
            logger.warning(f"Object '{obj}' not found in configuration. Ignoring it.")


async def console_reader(queue: asyncio.Queue):
    try:
        while True:
            obj = await aioconsole.ainput(">>")
            logger.debug(f"Received QR code: {obj}")
            await queue.put(obj)
            await asyncio.sleep(1)
    except EOFError:
        logger.error("Console reader task stopped")


async def main():
    parser = argparse.ArgumentParser(description="Stellarium API client")
    parser.add_argument("--conf", type=str, help="YAML configuration file")
    parser.add_argument("--log-level", type=str, help="Log level", default="INFO")
    args = parser.parse_args()

    if args.log_level.upper() in logging._nameToLevel:
        logger.setLevel(args.log_level.upper())

    with open(args.conf, "r") as file:
        conf = safe_load(file)

    scripts_path: str | None = None
    for p in conf["stellarium"]["script_paths"]:
        if os.path.exists(p):
            scripts_path = p
            break

    if not scripts_path:
        raise RuntimeError("No Stellarium scripts path found in configuration")

    client = Stellarium(
        scripts_path,
        conf["scripts"],
        port=conf["stellarium"]["port"],
    )

    global validator
    validator = NamesValidator(conf, scripts_path)

    if not await client.test():
        raise RuntimeError("Stellarium is not running")

    behavior = Behavior(conf["stellarium"]["behavior_previous_script"])
    timeout = conf["stellarium"]["timeout_previous_script"]
    valid_controls = {"console", "qrcode", "asr", "rfid"}
    controls = valid_controls.intersection(set(conf["controls"]))

    if not controls:
        raise RuntimeError(
            "No valid controls found in configuration, at least one is required"
        )

    queue = asyncio.Queue()

    tasks = []

    if "console" in controls:
        try:
            tasks.append(asyncio.create_task(console_reader(queue)))
        except Exception as e:
            logger.error(f"Error starting aioconsole: {e}")

    if "qrcode" in controls:
        try:
            qrcode = QRCodeReader(
                conf["qrcode_reader"]["device"],
                conf["qrcode_reader"]["buffer_size"],
            )
            qrcode.open()
            tasks.append(asyncio.create_task(qrcode.read(queue)))
        except Exception as e:
            logger.error(f"Error starting QR code reader: {e}")

    if len(tasks) == 0:
        raise RuntimeError(
            "Any of the controls in the configuration could be initialized, at least one is required"
        )

    tasks.append(
        asyncio.create_task(run_stellarium_script(queue, client, behavior, timeout))
    )

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
