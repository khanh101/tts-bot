import json
import os
import time
from typing import Any, Dict, List


class TtsConfig:
    def __init__(self, guild_id: str):
        self.guild_id: str = guild_id
        self.config_path: str = os.path.join("cfg", f"cfg_{guild_id}.json")
        self.last_voice_access: int = int(time.time())
        if not os.path.exists(self.config_path):
            self.__write_object({
                "tts_channel": "tts-bot",
                "lang": "vi",
                "voice_timeout": 1000,
                "resp_timeout": 15,
                "ban_list": [],
                "tts_path": f"tts_{guild_id}.mp3",
                "line_dir": "line",
                "emoji_dir": "emoji"
            })

    def __write_object(self, config: Dict[str, Any]):
        with open(self.config_path, "w") as fp:
            json.dump(config, fp, indent=2)

    def __read_object(self) -> Dict[str, Any]:
        with open(self.config_path, "r") as fp:
            return json.load(fp)

    def __get_tts_channel(self) -> str:
        return self.__read_object()["tts_channel"]

    tts_channel = property(__get_tts_channel)

    def __get_lang(self) -> str:
        return self.__read_object()["lang"]

    def __set_lang(self, lang: str):
        config = self.__read_object()
        config["lang"] = lang
        self.__write_object(config)

    lang = property(__get_lang, __set_lang)

    def __get_voice_timeout(self) -> str:
        return self.__read_object()["voice_timeout"]

    voice_timeout = property(__get_voice_timeout)

    def __get_resp_timeout(self) -> str:
        return self.__read_object()["resp_timeout"]

    resp_timeout = property(__get_resp_timeout)

    def __get_ban_list(self) -> List[str]:
        return self.__read_object()["ban_list"]

    ban_list = property(__get_ban_list)

    def __get_tts_path(self) -> str:
        return self.__read_object()["tts_path"]

    tts_path = property(__get_tts_path)

    def __get_line_dir(self) -> str:
        return self.__read_object()["line_dir"]

    line_dir = property(__get_line_dir)

    def __get_emoji_dir(self) -> str:
        return self.__read_object()["emoji_dir"]

    emoji_dir = property(__get_emoji_dir)

    def __get_lines(self) -> List[str]:
        return [".".join(filename.split('.')[:-1]) for filename in os.listdir(self.line_dir)]

    lines = property(__get_lines)

    def __get_emojis(self) -> List[str]:
        return [".".join(filename.split('.')[:-1]) for filename in os.listdir(self.emoji_dir)]

    emojis = property(__get_emojis)
