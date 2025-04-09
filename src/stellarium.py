import asyncio
import logging

import aiofiles
import httpx

logger = logging.getLogger("canismajor-stellarium")
try:
    from systemd import journal
    logger.propagate = False
    logger.addHandler(journal.JournaldLogHandler())
    logger.setLevel(logging.INFO)
except ImportError:
    ...



class Script:
    def __init__(self, template: str, script: str, delay1: float, delay2: float, final_fov: int):
        self.template = template
        self.script_path = script
        self.delay1 = delay1
        self.delay2 = delay2
        self.script = None
        self.final_fov = final_fov
        self.id = self.script_path.rstrip("/").split("/")[-1]

    async def ainit(self):
        if self.template:
            async with aiofiles.open(self.template, "r") as f:
                self.script = await f.read()
            self.script = self.script.replace("DELAY1", str(self.delay1))
            self.script = self.script.replace("DELAY2", str(self.delay2))
            self.script = self.script.replace("FINAL_FOV", str(self.final_fov))

    async def replace_and_save(self, name: list[str] | str):
        """
        Modifies the template and stores it in the script path.
        """
        if not self.script:
            await self.ainit()

        if self.template:
            objects = name if isinstance(name, list) else [name]
            modified_script = self.script.replace("OBJECTS_LIST", str(objects))

            async with aiofiles.open(self.script_path, "w") as f:
                await f.write(modified_script)


class Stellarium:
    def __init__(
        self,
        scripts: dict[str, dict[str, str]],
        url: str = "http://localhost",
        port: int = 8090,
    ):
        self.client = httpx.AsyncClient()
        self.url = f"{url}:{port}/api"
        self.scripts = {key: Script(**values) for key, values in scripts.items()}

    async def close(self):
        await self.client.aclose()

    async def get(self, endpoint: str):
        try:
            response = await self.client.get(f"{self.url}/{endpoint}")
            return response.json()
        except httpx.RequestError:
            logger.debug(f"Failed to fetch data from {self.url}/{endpoint}")
            return None
        except Exception:
            return response.text

    async def post(self, endpoint: str, data: dict | None = None):
        try:
            response = await self.client.post(f"{self.url}/{endpoint}", data=data)
            return response.json()
        except httpx.RequestError:
            logger.debug(f"Failed to post data to {self.url}/{endpoint}")
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

    async def is_script_running(self):
        status = await self.get("scripts/status")
        return status["scriptIsRunning"]

    async def wait_script_completion(self):
        while await self.is_script_running():
            await asyncio.sleep(1)

    async def stop_script(self):
        await self.post("scripts/stop")

    async def focus(self, name: str | None = None, typ: str = "constellation"):
        script = self.scripts.get(typ, None)
        if not script:
            logger.warning(f"Script {typ} not found")
            return
        await script.replace_and_save(name)
        await self.run_script(script.id)
