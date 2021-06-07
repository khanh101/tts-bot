import os
from typing import Dict, Callable, Any, Coroutine, Tuple

import discord

from handler.command import say_text, set_lang, say_special, TTS_CHANNEL, SPECIAL_FOLDER
from handler.config import Config

command: Dict[
    str,
    Tuple[Callable[[Config, discord.Client, discord.message.Message], Coroutine[Any, Any, None]], str],
] = {
}

command_with_args: Dict[
    str,
    Tuple[Callable[[Config, discord.Client, discord.message.Message, str], Coroutine[Any, Any, None]], str],
] = {
    "!say": (say_text, "!say <text>: say text"),
    "!set_lang": (set_lang, "!set_lang <lang>: set language"),
    "!special": (say_special, "!special <special>: say special"),
}

config: Dict[int, Config] = {}


async def help_command(config: Config, client: discord.Client, message: discord.message.Message):
    help_message = "HELP:\n"
    for _, desc in command.values():
        help_message += f"\t{desc}\n"
    for _, desc in command_with_args.values():
        help_message += f"\t{desc}\n"
    help_message += f"SETTINGS: {config.server_id}\n"
    for k, v in config.__dict__().items():
        help_message += f"\t{k}:{v}\n"
    help_message += "SPECIAL LIST:\n"
    for filename in os.listdir(SPECIAL_FOLDER):
        help_message += f"\t{'.'.join(filename.split('.')[:-1])}"

    await message.channel.send(help_message)


command["!howto"] = (help_command, "!howto: how to use")


async def handle_message(client: discord.Client, message: discord.Message):
    # filter out self message
    if message.author == client.user:
        return
    # filter out bot message
    if message.author.bot:
        return

    server_id = int(message.guild.id)

    if server_id not in config:
        config[server_id] = Config(server_id)

    # command
    for k in command.keys():
        if message.content == k:
            await command[k][0](config[server_id], client, message)
            return

    # command with args
    for k in command_with_args.keys():
        if message.content.startswith(k + " "):
            if len(message.content) < 1 + len(k):
                await message.channel.send("ERROR: Argument empty")
                continue
            text = message.content[1 + len(k):]
            await command_with_args[k][0](config[server_id], client, message, text)
            return

    # tts channel
    if message.channel.name == TTS_CHANNEL:
        await say_text(config[server_id], client, message, text=message.content)
        return
