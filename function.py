from typing import Optional, Callable, Any, Coroutine, Dict

import discord

from context import Context
from utils import LogType, log

Command = Callable[[Context], Coroutine[Any, Any, Optional[Any]]]
CommandwithArgs = Callable[[Context, Any], Coroutine[Any, Any, Optional[Any]]]

command_dict: Dict[str, Command] = {}
"""command"""
command_with_args_dict: Dict[str, CommandwithArgs] = {
}
"""command with arguments"""
default_command: Optional[Command] = None
"""default"""


def command(key: str):
    """command"""
    def create_command(f: Command) -> Command:
        command_dict[key] = f
        return f

    return create_command


def command_with_args(key: str):
    """command with args"""
    def create_command(f: CommandwithArgs) -> CommandwithArgs:
        command_with_args_dict[key] = f
        return f

    return create_command


def default(f: Command) -> Command:
    """default command"""
    global default_command
    if default_command is not None:
        raise Exception("default command must be set at most once")
    default_command = f
    return f


async def handle(ctx: Context):
    client, config, message = ctx
    """handle a message with config"""
    author: discord.member.Member = message.author
    # filter out self message
    if author == client.user:
        return
    # filter out bot message
    if author.bot:
        return

    # filter out empty message
    if len(message.content) == 0:
        return

    chunks = message.content.split(" ")
    # command
    if chunks[0] in command_dict.keys():
        await command_dict[chunks[0]](ctx)
        return
    # command with args
    if chunks[0] in command_with_args_dict.keys():
        if len(chunks) == 1:
            await log(ctx, LogType.Error, f"Command {chunks[0]}, argument empty!")
            return
        args = " ".join(chunks[1:])
        await command_with_args_dict[chunks[0]](ctx, args)
        return

    if default_command is not None:
        await default_command(ctx)
