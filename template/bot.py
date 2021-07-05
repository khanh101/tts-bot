from typing import Optional, Callable, Any, Coroutine, Iterable, Dict

import discord

from template.context import Context

Command = Callable[[Context], Coroutine[Any, Any, Optional[Any]]]
CommandWithArgs = Callable[[Context, Any], Coroutine[Any, Any, Optional[Any]]]


class Bot:
    """
    Bot : contains template config
    """

    def __init__(self):
        self.default: Optional[Command] = None
        self.command_dict: Dict[str, Command] = {}
        self.command_with_args_dict: Dict[str, CommandWithArgs] = {}

    def __repr__(self) -> str:
        out = ""
        out += "COMMAND\n"
        for k, f in self.command_dict.items():
            out += f"\t{k} : {f.__doc__}\n"
        out += "\n"
        out += "COMMAND WITH ARGS\n"
        for k, f in self.command_with_args_dict.items():
            out += f"\t{k} <args> : {f.__doc__}\n"
        out += "\n"
        out += "DEFAULT\n"
        out += f"default : {self.default.__doc__}\n"
        return out

    def set_default(self, cmd: Command):
        self.default = cmd

    def set_command(self, key: str, cmd: Command):
        self.command_dict[key] = cmd

    def set_command_with_args(self, key: str, cmd: CommandWithArgs):
        self.command_with_args_dict[key] = cmd
