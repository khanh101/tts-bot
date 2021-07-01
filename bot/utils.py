import json
import os
from typing import Any, Dict, Optional


class JsonObject:
    """
    JsonObject : a wrapper for a json file
    """

    def __init__(self, config_path: str, default: Optional[Any] = None):
        if default is None:
            default = {}
        self.__config_path: str = config_path
        self.__default_object: Any = default

    def __ensure(self):
        if not os.path.exists(self.__config_path):
            self.__write(self.__default_object)

    def __getitem__(self, key: str) -> Any:
        return self.__read()[key]

    def __setitem__(self, key: str, value: Any):
        config = self.__read()
        config[key] = value
        self.__write(config)

    def __dict__(self) -> Dict[str, Any]:
        return self.__read()

    def __write(self, config: Dict[str, Any]):
        with open(self.__config_path, "w") as f:
            json.dump(config, f, indent=4)

    def __read(self) -> Dict[str, Any]:
        self.__ensure()
        with open(self.__config_path, "r") as f:
            return json.load(f)

