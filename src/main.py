import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor

from yaml import safe_load

from speech import SpeechMatch


async def select_object(queue: asyncio.Queue):
    while True:
        obj = await queue.get()
        print(f"Selected object: {obj}")
        await asyncio.sleep(0.5)
        queue.task_done()

async def main():
    parser = argparse.ArgumentParser(description="Stellarium API client")
    parser.add_argument("--conf", type=str, help="YAML configuration file")
    args = parser.parse_args()

    with open(args.conf, "r") as file:
        conf = safe_load(file)

    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    speech = SpeechMatch(conf["stellarium_objects"])
    with ThreadPoolExecutor() as pool:
        loop.run_in_executor(pool, speech.listen, queue, loop)
        await select_object(queue)


if __name__ == "__main__":
    asyncio.run(main())
