import asyncio
import logging
from enum import StrEnum

import aiofiles
import httpx

logger = logging.getLogger(__name__)

class Script:
    def __init__(self, template: str, script_path: str, delay1: int, delay2: int):
        self.template = template
        self.script_path = script_path
        self.delay1 = delay1
        self.delay2 = delay2
        self.script = None
        self.id = self.script_path.rstrip("/").split("/")[-1]

    async def ainit(self):
        async with aiofiles.open(self.template, "r") as f:
            self.script = await f.read()
        self.script = self.script.replace("DELAY1", str(self.delay1))
        self.script = self.script.replace("DELAY2", str(self.delay2))

    async def replace_and_save(self, name: list[str] | str):
        """
        Modifies the template and stores it in the script path.
        """
        if not self.script:
            await self.ainit()

        objects = name if isinstance(name, list) else [name]
        modified_script = self.script.replace("OBJECTS_LIST", str(objects))

        async with aiofiles.open(self.script_path, "w") as f:
            await f.write(modified_script)


class Stellarium:
    def __init__(
        self,
        const_script: str,
        const_template: str,
        const_delay1: int,
        const_delay2: int,
        planets_script: str,
        planets_template: str,
        planets_delay1: int,
        planets_delay2: int,
        url: str = "http://localhost",
        port: int = 8090,
    ):
        self.client = httpx.AsyncClient()
        self.url = f"{url}:{port}/api"
        self.const_script = Script(
            const_template, const_script, const_delay1, const_delay2
        )
        self.planets_script = Script(
            planets_template, planets_script, planets_delay1, planets_delay2
        )

    async def close(self):
        await self.client.aclose()

    async def get(self, endpoint: str):
        try:
            response = await self.client.get(f"{self.url}/{endpoint}")
            return response.json()
        except httpx.RequestError:
            logger.warning(f"Failed to fetch data from {self.url}/{endpoint}")
            return None
        except Exception:
            return response.text

    async def post(self, endpoint: str, data: dict | None = None):
        try:
            response = await self.client.post(f"{self.url}/{endpoint}", data=data)
            return response.json()
        except httpx.RequestError:
            logger.warning(f"Failed to post data to {self.url}/{endpoint}")
            return None
        except Exception:  # JSONDecoderError:
            return response.text

    async def test(self):
        try:
            return await self.get("main/status") is not None
        except Exception:
            return False

    async def get_status(self):
        return await self.get("main/status")

    async def run_script(self, script_id: str):
        await self.post("scripts/run", {"id": script_id})

    async def focus(self, name: str, typ: str = "constellation"):
        if typ == "constellation":
            await self.const_script.replace_and_save(name)
            await self.run_script(self.const_script.id)
        elif typ == "planet":
            await self.planets_script.replace_and_save(name)
            await self.run_script(self.planets_script.id)