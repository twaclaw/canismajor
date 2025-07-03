import asyncio
import logging
import os
from enum import Enum, StrEnum, auto
from json.decoder import JSONDecodeError
from typing import Any

import aiofiles
import httpx

logger = logging.getLogger("canismajor")


constellations = {
    "Andromeda": "Chained Maiden",
    "Antlia": "Air Pump",
    "Apus": "Bird of Paradise",
    "Aquarius": "Water Bearer",
    "Aquila": "Eagle",
    "Ara": "Altar",
    "Aries": "Ram",
    "Auriga": "Charioteer",
    "Bootes": "Herdsman",
    "Caelum": "Engraving Tool",
    "Camelopardalis": "Giraffe",
    "Cancer": "Crab",
    "Canes Venatici": "Hunting Dogs",
    "Canis Major": "Great Dog",
    "Canis Minor": "Lesser Dog",
    "Capricornus": "Sea Goat",
    "Carina": "Keel",
    "Cassiopeia": "Seated Queen",
    "Centaurus": "Centaur",
    "Cepheus": "King",
    "Cetus": "Sea Monster",
    "Chamaeleon": "Chameleon",
    "Circinus": "Compass",
    "Columba": "Dove",
    "Coma Berenices": "Berenice's Hair Clip",
    "Corona Australis": "Southern Crown",
    "Corona Borealis": "Northern Crown",
    "Corvus": "Crow",
    "Crater": "Cup",
    "Crux": "Southern Cross",
    "Cygnus": "Swan",
    "Delphinus": "Dolphin",
    "Dorado": "Swordfish",
    "Draco": "Dragon",
    "Equuleus": "Little Horse",
    "Eridanus": "River",
    "Fornax": "Furnace",
    "Gemini": "Twins",
    "Grus": "Crane",
    "Hercules": "Hercules",
    "Horologium": "Clock",
    "Hydra": "Female Water Snake",
    "Hydrus": "Male Water Snake",
    "Indus": "Indian",
    "Lacerta": "Lizard",
    "Leo": "Lion",
    "Leo Minor": "Lesser Lion",
    "Lepus": "Hare",
    "Libra": "Scales",
    "Lupus": "Wolf",
    "Lynx": "Lynx",
    "Lyra": "Lyre",
    "Mensa": "Table Mountain",
    "Microscopium": "Microscope",
    "Monoceros": "Unicorn",
    "Musca": "Fly",
    "Norma": "Carpenter's Square",
    "Octans": "Octant",
    "Ophiuchus": "Serpent Bearer",
    "Orion": "Hunter",
    "Pavo": "Peacock",
    "Pegasus": "Winged Horse",
    "Perseus": "Hero",
    "Phoenix": "Phoenix",
    "Pictor": "Painter's Easel",
    "Pisces": "Fishes",
    "Piscis Austrinus": "Southern Fish",
    "Puppis": "Stern",
    "Pyxis": "Mariner Compass",
    "Reticulum": "Reticle",
    "Sagitta": "Arrow",
    "Sagittarius": "Archer",
    "Scorpius": "Scorpion",
    "Sculptor": "Sculptor",
    "Scutum": "Shield",
    "Serpens": "Serpent",
    "Sextans": "Sextant",
    "Taurus": "Bull",
    "Telescopium": "Telescope",
    "Triangulum": "Triangle",
    "Triangulum Australe": "Southern Triangle",
    "Tucana": "Toucan",
    "Ursa Major": "Big Dipper (Plough)",
    "Ursa Minor": "Little Dipper",
    "Vela": "Sails",
    "Virgo": "Maiden",
    "Volans": "Flying Fish",
    "Vulpecula": "Fox",
}


class Behavior(StrEnum):
    """
    Defines what to do with a running script when a  new object arrives in the queue.
    """

    STOP = "stop"
    IGNORE = "ignore"
    WAIT = "wait"


class ScriptType(Enum):
    """
    - STELLARIUM_SCRIPT: Scripts included in the Stellarium distribution. Run without modifications.
    - STANDALONE_SCRIPT: Custom script with no parameters
    - PARAMS_SCRIPT_CONSTELLATIONS: Custom script received a list of  constellations as input
    - PARAMS_SCRIPT_OBJECTS: Custom script received a list of objects as input
    """

    STELLARIUM_SCRIPT = auto()
    STANDALONE_SCRIPT = auto()
    PARAMS_SCRIPT_CONSTELLATIONS = auto()
    PARAMS_SCRIPT_OBJECTS = auto()


class NamesValidator:
    """
    Validates the objects names before passing them to Stellarium,
    and introspects the kind of script to run based on the object name.
    """

    def __init__(self, conf: dict[str, Any], stellarium_scripts_path: str):
        self.language = conf["stellarium"]["constellations_language"]
        if self.language not in ["english", "native"]:
            raise RuntimeError(
                "Invalid language for constellations, must be 'english' or 'native'"
            )
        self.objects = conf["search"]["objects"]
        self.stellarium_scripts_path = stellarium_scripts_path
        self.standalone_scripts = [
            k for k in conf["scripts"].keys() if k not in ["constellation", "object"]
        ]

    def validate(self, obj) -> tuple[str, ScriptType] | None:
        """
        Introspects the kind of script to run based on the object name.

        Returns:
        - Object name: str
        - Script type: ScriptType
        """

        obj_title = obj.title()

        if obj_title in self.objects:
            return obj_title, ScriptType.PARAMS_SCRIPT_OBJECTS

        if obj in self.standalone_scripts:
            return obj, ScriptType.STANDALONE_SCRIPT

        if obj_title in constellations:
            return (
                constellations[obj_title] if self.language == "english" else obj_title,
                ScriptType.PARAMS_SCRIPT_CONSTELLATIONS,
            )

        if obj in os.listdir(self.stellarium_scripts_path):
            return obj, ScriptType.STELLARIUM_SCRIPT

        return None


class Script:
    def __init__(
        self,
        scripts_path: str,
        script_name: str,
        common_header: str,
        args: dict[str, Any],
    ):
        self.template = f"templates/{script_name}"
        self.script_path = f"{scripts_path}/{script_name}"
        self.args = args
        self.script = None
        self.id = script_name
        self.common_header = common_header

    async def ainit(self):
        if not self.template:
            raise RuntimeError("Template path is not set. Cannot initialize script.")

        async with aiofiles.open(self.template, "r") as f:
            self.script = await f.read()

        self.script = self.script.replace("_COMMON_SCRIPT", self.common_header)
        for arg, value in self.args.items():
            if isinstance(value, list):
                value = ", ".join(
                    f'"{constellations.get(item, item)}"' for item in value
                )
                value = f"new Array({value})"
            else:
                value = str(value).lower() if isinstance(value, bool) else str(value)
            self.script = self.script.replace(arg, value)

    async def replace_and_save(
        self, objects: list[str], audio: list[str] | None = None
    ):
        """
        Modifies the template and stores it in the script path.
        """
        if not self.script:
            await self.ainit()
        objects_list = ", ".join(f'"{item}"' for item in objects)
        modified_script = self.script.replace(
            "_OBJECTS_LIST", f"new Array({objects_list})"
        )

        audio_list = ", ".join(f'"{item}"' for item in audio) if audio else "[]"
        modified_script = modified_script.replace("_AUDIO", f"new Array({audio_list})")

        async with aiofiles.open(self.script_path, "w") as f:
            await f.write(modified_script)


class Stellarium:
    def __init__(
        self,
        conf: dict[str, Any],
        url: str = "http://localhost",
    ):
        self.client = httpx.AsyncClient()
        self.conf = conf
        port = conf["stellarium"]["port"]
        self.url = f"{url}:{port}/api"
        self.language = conf["stellarium"]["constellations_language"]
        self.const_english = {constellations[k]: k for k in constellations}

        scripts_path: str | None = None
        for p in conf["stellarium"]["script_paths"]:
            if os.path.exists(p):
                scripts_path = p
                break

        if not scripts_path:
            raise RuntimeError("No Stellarium scripts path found in configuration")

        self.scripts_path = scripts_path

        audio_symlink = os.path.join(self.scripts_path, "audio")
        audio_target = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "audio")
        )
        if not os.path.islink(audio_symlink):
            if os.path.exists(audio_symlink):
                os.remove(audio_symlink)
            os.symlink(audio_target, audio_symlink)

        scripts = conf["scripts"]

        self.common_header = self.conf.get(
            "scripts_common_header", "_canismajor_common.inc"
        )
        self.scripts = {
            key: Script(
                **(
                    {"scripts_path": scripts_path, "common_header": self.common_header}
                    | values
                )
            )
            for key, values in scripts.items()
        }

        self.validator = NamesValidator(conf, scripts_path)
        self.behavior_previous_script = Behavior(
            conf["stellarium"].get("behavior_previous_script", "wait")
        )
        self.timeout_previous_script = conf["stellarium"].get(
            "timeout_previous_script", 60.0
        )

        self.playsound = conf["stellarium"].get("playsound", False)
        self.zodiac = [
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpius",
            "Ophiuchus",
            "Sagittarius",
            "Capricornus",
            "Aquarius",
            "Pisces",
            "Aries",
            "Taurus",
        ]

        if self.playsound:
            try:
                self.audiofiles = {k: f"audio/{k}.mp3" for k in constellations} | {
                    k: f"audio/{k}.mp3" for k in self.conf["search"]["objects"]
                }
            except Exception:
                self.playsound = False

    async def ainit(self):
        """
        Copies the common script containing boilerplate initialization code
        """
        async with aiofiles.open(f"templates/{self.common_header}", "r") as f:
            common_header = await f.read()

        async with aiofiles.open(f"{self.scripts_path}/{self.common_header}", "w") as f:
            await f.write(common_header)

    async def _close(self):
        await self.client.aclose()

    async def _get(self, endpoint: str):
        try:
            response = await self.client.get(f"{self.url}/{endpoint}")
            return response.json()
        except httpx.RequestError:
            logger.debug(f"Failed to fetch data from {self.url}/{endpoint}")
            return None
        except JSONDecodeError:
            return response.text

    async def _post(self, endpoint: str, data: dict | None = None):
        try:
            response = await self.client.post(f"{self.url}/{endpoint}", data=data)
            return response.json()
        except httpx.RequestError:
            logger.debug(f"Failed to post data to {self.url}/{endpoint}")
            return None
        except JSONDecodeError:
            return response.text

    async def _run_script(self, script_id: str):
        await self._post("scripts/run", {"id": script_id})

    async def _is_script_running(self):
        status = await self._get("scripts/status")
        return status["scriptIsRunning"]

    async def _wait_script_completion(self):
        while await self._is_script_running():
            await asyncio.sleep(1)

    async def _stop_script(self):
        await self._post("scripts/stop")

    def _get_audio_file(self, sound: str) -> list[str] | None:
        audio_files = [
            self.audiofiles.get(self.const_english.get(s, s), None) for s in sound
        ]
        audio_files = list(filter(None, audio_files))
        return audio_files

    async def _focus(
        self, param: str | None = None, script_type: ScriptType | None = None
    ):
        """
        Focuses Stellarium on the given object. This is achieved by running a script
        depending on the type of object (e.g., constellation, planet, etc).
        """
        if script_type is ScriptType.STELLARIUM_SCRIPT:
            await self._run_script(param)
            return

        audio: list[str] | None = None

        if script_type is ScriptType.STANDALONE_SCRIPT:
            script = self.scripts.get(param)
            if param == "zodiac2":
                param = self.zodiac
            elif param == "earth2":
                param = self.zodiac
            else:
                consts = self.conf["scripts"][param]["args"].get("_OBJECTS_LIST", [])
                audio = self._get_audio_file(consts)

        elif script_type is ScriptType.PARAMS_SCRIPT_OBJECTS:
            audio = self._get_audio_file([param])
            script = self.scripts.get("object")
        else:
            audio = self._get_audio_file([param])
            script = self.scripts.get("constellation")

        if not script:
            logger.warning("Script not found")
            return

        if self.language == "english":
            param = (
                [constellations.get(obj, obj) for obj in param]
                if isinstance(param, list)
                else [constellations.get(param, param)]
            )

        await script.replace_and_save(param, audio if audio else None)
        await self._run_script(script.id)

    async def test(self):
        response = await self._get("main/status")
        return response is not None

    async def run_script_task(self, queue: asyncio.Queue):
        while True:
            obj = await queue.get()
            logger.debug(f"Received object in queue: {obj}")
            res = self.validator.validate(obj)
            if not res:
                logger.warning(f"Object '{obj}' not found in configuration.")
                queue.task_done()
                continue

            obj, typ = res
            logger.debug(f"Object '{obj}' found in configuration. Type: {typ}")
            if self.behavior_previous_script == Behavior.STOP:
                await self._stop_script()
            elif self.behavior_previous_script == Behavior.WAIT:
                try:
                    await asyncio.wait_for(
                        self._wait_script_completion(),
                        timeout=self.timeout_previous_script,
                    )
                except asyncio.TimeoutError:
                    await self._stop_script()

            if not await self._is_script_running():
                await self._focus(obj, typ)
            queue.task_done()
