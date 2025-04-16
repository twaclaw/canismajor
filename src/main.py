import argparse
import asyncio
import logging

import aioconsole
from yaml import safe_load

from hid import QRCodeReader
from stellarium import Stellarium

logger = logging.getLogger("canismajor")

try:
    from systemd import journal

    logger.propagate = False
    logger.addHandler(journal.JournaldLogHandler())
except ImportError:
    ...


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
    parser.add_argument(
        "--conf", type=str, help="YAML configuration file", required=True
    )
    parser.add_argument("--log-level", type=str, help="Log level", default="INFO")
    args = parser.parse_args()

    if args.log_level.upper() in logging._nameToLevel:
        logger.setLevel(args.log_level.upper())

    with open(args.conf, "r") as file:
        conf = safe_load(file)

    valid_controls = {"console", "qrcode", "asr", "rfid"}
    controls = valid_controls.intersection(set(conf["controls"]))

    if not controls:
        raise RuntimeError(
            "No valid controls found in configuration, at least one is required"
        )

    client = Stellarium(conf)

    if not await client.test():
        raise RuntimeError("Stellarium is not running")

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

    tasks.append(asyncio.create_task(client.run_script_task(queue)))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
