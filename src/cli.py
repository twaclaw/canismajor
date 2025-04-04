import argparse
import asyncio

from yaml import safe_load

from stellarium import Stellarium


async def main():
    parser = argparse.ArgumentParser(description="Stellarium API client")
    parser.add_argument(
        "--conf", type=str, help="YAML configuration file", default="config.yaml"
    )
    parser.add_argument(
        "--name", type=str, help="Name of the cellestial object to focus on"
    )
    parser.add_argument("--type", type=str, help="Type of the cellestial object to focus on", default="constellation")

    args = parser.parse_args()

    with open(args.conf, "r") as file:
        conf = safe_load(file)

    const = conf["scripts"]["constellations"]
    planets = conf["scripts"]["planets"]

    client = Stellarium(
        const["script"],
        const["template"],
        const["delay1"],
        const["delay2"],
        planets["script"],
        planets["template"],
        planets["delay1"],
        planets["delay2"],
        port=conf["stellarium"]["port"],
    )

    await client.focus(args.name)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
