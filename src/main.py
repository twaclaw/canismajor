import argparse
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from enum import StrEnum

import aioconsole
from yaml import safe_load

from stellarium import Stellarium

try:
    from speech import SpeechMatch
except ImportError:
    ...

logger = logging.getLogger(__name__)


class Behavior(StrEnum):
    """
    Defines what to do with a running script when a  new object arrives in the queue.
    """

    STOP = "stop"
    IGNORE = "ignore"
    WAIT = "wait"


class Validator:
    def __init__(self, conf):
        self.languate = conf["stellarium"]["objects_language"]
        self.objects = conf["objects"]["objects"]
        self.direct_scripts = [
            k for k in conf["scripts"].keys() if k not in ["constellation", "object"]
        ]
        if self.languate == "english":
            self.constellations = conf["objects"]["constellations"].values()
        else:
            self.constellations = conf["objects"]["constellations"].keys()

    def validate(self, obj) -> tuple[str, str] | None:
        if obj in self.constellations:
            return obj, "constellation"
        if obj in self.objects:
            return obj, "object"
        if obj in self.direct_scripts:
            return obj, "direct_script"

        return None


validator: Validator | None = None


async def run_stellarium_script(
    queue: asyncio.Queue, client: Stellarium, behavior: Behavior, timeout: float
):
    global validator
    assert validator
    while True:
        obj = await queue.get()
        res = validator.validate(obj)
        if res:
            obj, typ = res
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


async def qr_code_reader(queue):
    while True:
        obj = await aioconsole.ainput(">>")
        await queue.put(obj)
        await asyncio.sleep(1)


async def main():
    parser = argparse.ArgumentParser(description="Stellarium API client")
    parser.add_argument("--conf", type=str, help="YAML configuration file")
    args = parser.parse_args()

    with open(args.conf, "r") as file:
        conf = safe_load(file)

    client = Stellarium(
        conf["scripts"],
        port=conf["stellarium"]["port"],
    )
    global validator
    validator = Validator(conf)

    if not await client.test():
        raise RuntimeError("Stellarium is not running")

    behavior = Behavior(conf["stellarium"]["behavior_previous_script"])
    timeout = conf["stellarium"]["timeout_previous_script"]
    controls = {"qrcode", "asr", "rfid"}.intersection(set(conf["controls"]))
    if not controls:
        raise RuntimeError("No control options found in configuration")

    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()  # check if required

    tasks = []
    tasks.append(
        asyncio.create_task(run_stellarium_script(queue, client, behavior, timeout))
    )

    if "asr" in controls:
        with ThreadPoolExecutor() as pool:
            speech = SpeechMatch(
                conf["stellarium_objects"], conf["stellarium"]["objects_language"]
            )
            loop.run_in_executor(pool, speech.listen, queue, loop)

    if "qrcode" in controls:
        tasks.append(asyncio.create_task(qr_code_reader(queue)))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
