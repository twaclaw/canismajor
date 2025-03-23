import asyncio
import logging
from enum import StrEnum

import httpx

logger = logging.getLogger(__name__)


class Feature(StrEnum):
    CONST_LINES = "constellation_lines"
    CONST_ART = "constellation_art"
    CONST_LABELS = "constellation_labels"
    CONST_BOUNDARIES = "constellation_boundaries"
    ATMOSPHERE = "atmosphere"
    NIGHT_MODE = "night_mode"
    PLANETS_LABELS = "planets_labels"
    GROUND = "ground"


class Stellarium:
    def __init__(self, url: str = "http://localhost", port: int = 8090):
        self.client = httpx.AsyncClient()
        self.url = f"{url}:{port}/api"

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
        except Exception: #JSONDecoderError:
            return response.text

    async def test(self):
        try:
            return await self.get("main/status") is not None
        except Exception:
            return False

    async def focus(self, name: str, mode: str = "center", unfocus: bool = True):
        name = name.title()
        names = await self.get(f"objects/find?str={name}")
        if names:
            await self.post("main/focus", {"target": name, "mode": mode})
            if unfocus:
                await self.unfocus()

    async def unfocus(self):
        return await self.post("main/focus")


    async def toggle_visibility(self, feature: Feature, state: bool):
        response = await self.post(
            "stelaction/do", {"id": f"actionShow_{feature.title()}"}
        )
        if response is state:
            return response

        return await self.post("stelaction/do", {"id": f"actionShow_{feature.title()}"})

    async def get_fov(self) -> float:
        response = await self.get("main/status")
        return response["view"]["fov"]

    async def get_status(self):
        return await self.get("main/status")

    async def get_focused_object_type(self) -> str:
        status = await self.get("objects/info")
        return "constellation" if "constellation" in status else "object"

    async def set_fov(self, fov: float):
        return await self.post("main/fov", {"fov": fov})

    async def zoom(self, factor: float, t: float = 3):
        fov = await self.get_fov()
        return await self.post("scripts/direct", {"code": f"StelMovementMgr.zoomTo({fov*factor}, {t})"})


    async def focus_animation(self, name: str, delay: int = 5, initial_fov: float = 60):
        await self.default_visibility()
        await self.set_fov(initial_fov)
        await self.focus(name, "center", False)
        object_type = await self.get_focused_object_type()
        await self.unfocus()

        if object_type == "constellation":
            await asyncio.sleep(delay)
            await self.toggle_visibility(Feature.CONST_LINES, True)
            await asyncio.sleep(delay)
            await self.toggle_visibility(Feature.CONST_ART, True)
            await asyncio.sleep(delay)
            await self.set_fov(initial_fov)
        else:
            await asyncio.sleep(delay)
            await self.toggle_visibility(Feature.PLANETS_LABELS, False)
            await self.focus(name, "zoom")
            await asyncio.sleep(delay)
            zoom_factor = 0.1
            await self.zoom(zoom_factor, 3)
            await asyncio.sleep(delay)
            await self.zoom(initial_fov/zoom_factor, 3)

    async def ainit(self) -> bool:
        ok = await self.test()
        if not ok:
            logger.error(f"Failed to connect to {self.url}")
            return False

        await self.default_visibility()
        return True

    async def default_visibility(self):
        await self.toggle_visibility(Feature.CONST_LINES, False)
        await self.toggle_visibility(Feature.CONST_ART, False)
        await self.toggle_visibility(Feature.CONST_LABELS, False)
        await self.toggle_visibility(Feature.CONST_BOUNDARIES, False)
        await self.toggle_visibility(Feature.ATMOSPHERE, False)
        await self.toggle_visibility(Feature.NIGHT_MODE, False)
        await self.toggle_visibility(Feature.PLANETS_LABELS, True)
        await self.toggle_visibility(Feature.GROUND, False)
        return True
