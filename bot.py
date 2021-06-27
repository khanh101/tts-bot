import json
import os
from typing import Dict, Any, Optional, List

import discord


class Config:
    """
    Config: a wrapper for a json file
    """
    def __init__(self, server_id: str):
        self.server_id: str = server_id

    def __ensure(self):
        if not os.path.exists("cfg"):
            os.mkdir("cfg")
        if not os.path.exists("line"):
            os.mkdir("line")
        if not os.path.exists(self.__get_config_path()):
            self.__write({
                "tts_channel": "tts-bot",
                "lang": "vi",
                "voice_timeout": 3600,
                "log_timeout": 30,
                "ban_list": [],
                "tts_path": f"tts_{self.server_id}.mp3",
                "line_dir": "line",
            })

    def __getitem__(self, key: str) -> Any:
        return self.__read()[key]

    def __setitem__(self, key: str, value: Any):
        config = self.__read()
        config[key] = value
        self.__write(config)

    def __dict__(self) -> Dict[str, Any]:
        config = self.__read()
        return {
            "tts_channel": config["tts_channel"],
            "lang": config["lang"],
            "voice_timeout": config["voice_timeout"],
            "log_timeout": config["log_timeout"],
            "ban_list": config["ban_list"],
        }

    def __get_config_path(self) -> str:
        return os.path.join("cfg", f"cfg_{self.server_id}.json")

    def __write(self, config: Dict[str, Any]):
        with open(self.__get_config_path(), "w") as f:
            json.dump(config, f, indent=4)

    def __read(self) -> Dict[str, Any]:
        self.__ensure()
        with open(self.__get_config_path(), "r") as f:
            return json.load(f)


class Bot:
    """
    Bot : a pair of discord.Client and server_id. Bot contains server's config and other properties
    """
    def __init__(self, client: discord.Client, server_id: str):
        self.client: discord.Client = client
        self.server_id: str = server_id
        self.config: Config = Config(server_id)
        self.last_voice_access: Optional[int] = None

    def get_lines(self) -> List[str]:
        return [".".join(filename.split('.')[:-1]) for filename in os.listdir(self.config["line_dir"])]
