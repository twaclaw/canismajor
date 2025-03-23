import argparse
import asyncio

from stellarium import Stellarium


async def main():
    parser = argparse.ArgumentParser(description="Stellarium API client")
    parser.add_argument(
        "--focus", type=str, help="Name of the cellestial object to focus on"
    )
    args = parser.parse_args()

    client = Stellarium(port=8091)
    # if not await client.test():
        # return

    # fov = await client.get_fov()

    await client.focus_animation(args.focus)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
