from typing import Optional, Callable, Any, Coroutine, Iterable

import discord


class Config:
    """Config : Server configurations"""
    pass


class Bot:
    """Bot : Bot configurations"""

    def __init__(self):
        self.command_dict = {}
        self.command_with_args_dict = {}
        self.default = None

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


class Context:
    """
    Context : Context of a message
    """

    def __init__(self, bot: Bot, client: discord.Client, config: Config, message: discord.Message):
        self.bot = bot
        self.client = client
        self.config = config
        self.message = message

    def __iter__(self) -> Iterable[Any]:
        return iter((self.bot, self.client, self.config, self.message))


Command = Callable[[Context], Coroutine[Any, Any, Optional[Any]]]
CommandwithArgs = Callable[[Context, Any], Coroutine[Any, Any, Optional[Any]]]


def command(bot: Bot, key: str):
    """command"""

    def __new_command(f: Command) -> Command:
        bot.command_dict[key] = f
        return f

    return __new_command


def command_with_args(bot: Bot, key: str):
    """command with args"""

    def __new_command(f: CommandwithArgs) -> CommandwithArgs:
        bot.command_with_args_dict[key] = f
        return f

    return __new_command


def default(bot: Bot):
    def __new_command(f: Command) -> Command:
        """default command"""
        if bot.default is not None:
            raise Exception("default command must be set at most once")
        bot.default = f
        return f

    return __new_command


async def handle(ctx: Context):
    bot, client, config, message = ctx
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
    if chunks[0] in bot.command_dict.keys():
        await bot.command_dict[chunks[0]](ctx)
        return
    # command with args
    if chunks[0] in bot.command_with_args_dict.keys():
        if len(chunks) > 1:
            args = " ".join(chunks[1:])
            await bot.command_with_args_dict[chunks[0]](ctx, args)
            return

    if bot.default is not None:
        await bot.default(ctx)
