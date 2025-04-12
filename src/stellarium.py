import asyncio
import logging
from enum import Enum, auto
from typing import Any

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


class ScriptType(Enum):
    """
    - STELLARIUM_SCRIPT: Scripts included in the Stellarium distribution. Run as they are.
    - STANDALONE_SCRIPT: Custom script with no parameters
    - PARAMS_SCRIPT_CONSTELLATIONS: Custom script received a list of  constellations as input
    - PARAMS_SCRIPT_OBJECTS: Custom script received a list of objects as input
    """

    STELLARIUM_SCRIPT = auto()
    STANDALONE_SCRIPT = auto()
    PARAMS_SCRIPT_CONSTELLATIONS = auto()
    PARAMS_SCRIPT_OBJECTS = auto()


class Script:
    def __init__(self, scripts_path: str, script_name: str, args: dict[str, Any]):
        self.template = f"templates/{script_name}"
        self.script_path = f"{scripts_path}/{script_name}"
        self.args = args
        self.script = None
        self.id = script_name

    async def ainit(self):
        if self.template:
            async with aiofiles.open(self.template, "r") as f:
                self.script = await f.read()

            for arg in self.args:
                value = self.args[arg]
                if isinstance(value, bool):
                    value = str(value).lower()
                else:
                    value = str(value)

                self.script = self.script.replace(arg, value)

    async def replace_and_save(self, name: list[str] | str):
        """
        Modifies the template and stores it in the script path.
        """
        if not self.script:
            await self.ainit()

        if self.template:
            objects = name if isinstance(name, list) else [name]
            objects_list = ", ".join(f'"{item}"' for item in objects)
            modified_script = self.script.replace(
                "_OBJECTS_LIST", f"new Array({objects_list})"
            )

            async with aiofiles.open(self.script_path, "w") as f:
                await f.write(modified_script)


class Stellarium:
    def __init__(
        self,
        scripts_path: str,
        scripts: dict[str, dict[str, str]],
        url: str = "http://localhost",
        port: int = 8090,
    ):
        self.client = httpx.AsyncClient()
        self.url = f"{url}:{port}/api"
        self.scripts = {}
        self.scripts = {
            key: Script(**({"scripts_path": scripts_path} | values))
            for key, values in scripts.items()
        }

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

    async def focus(
        self, param: str | None = None, script_type: ScriptType | None = None
    ):
        if script_type is ScriptType.STELLARIUM_SCRIPT:
            await self.run_script(param)

        if script_type is ScriptType.STANDALONE_SCRIPT:
            script = self.scripts.get(param, None)
        elif script_type is ScriptType.PARAMS_SCRIPT_OBJECTS:
            script = self.scripts.get("object", None)
        else:
            script = self.scripts.get("constellation", None)

        if not script:
            logger.warning("Script not found")
            return

        if script_type in [
            ScriptType.PARAMS_SCRIPT_CONSTELLATIONS,
            ScriptType.PARAMS_SCRIPT_OBJECTS,
        ]:
            await script.replace_and_save(param)
        await self.run_script(script.id)
