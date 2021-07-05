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

    def set_default(self, cmd: Command):
        print(f"set default: {cmd.__doc__}")
        self.default = cmd

    def set_command(self, key: str, cmd: Command):
        print(f"set command {key}: {cmd.__doc__}")
        self.command_dict[key] = cmd

    def set_command_with_args(self, key: str, cmd: CommandWithArgs):
        print(f"set command with args {key}: {cmd.__doc__}")
        self.command_with_args_dict[key] = cmd
