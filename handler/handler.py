import os
from typing import Dict

import discord

from handler.ban import is_banned, BAN_FILENAME
from handler.command import say_text, set_lang, say_line, TTS_CHANNEL, LINE_FOLDERNAME
from handler.config import Config

command = {
}

command_with_args = {
    "!say": say_text,
    "!lang": set_lang,
    "!line": say_line,
}

config_dict: Dict[int, Config] = {}


async def howto(config: Config, client: discord.Client, message: discord.message.Message):
    """!howto: help"""
    help_message = "HELP:\n"
    for f in command.values():
        help_message += f"\t{f.__doc__}\n"
    for f in command_with_args.values():
        help_message += f"\t{f.__doc__}\n"
    help_message += f"SETTINGS: {config.server_id}\n"
    for k, v in config.__dict__().items():
        help_message += f"\t{k}:{v}\n"
    help_message += "LINE AVAILABLE:\n"
    for filename in os.listdir(LINE_FOLDERNAME):
        help_message += f"\t{'.'.join(filename.split('.')[:-1])}"
    help_message += "\n"
    help_message += "BAN LIST:\n"
    with open(BAN_FILENAME, "r") as f:
        for line in f.readlines():
            line = line[:-1] if line[-1] == "\n" else line
            help_message += f"\t{line}"

    await message.channel.send(help_message)


command["!howto"] = howto


async def handle_message(client: discord.Client, message: discord.Message):
    # filter out self message
    if message.author == client.user:
        return
    # filter out bot message
    if message.author.bot:
        return
    server_id = int(message.guild.id)

    # create config if not exists
    if server_id not in config_dict:
        config_dict[server_id] = Config(server_id)

    # command
    for k in command.keys():
        if message.content == k:
            # filter out blocked user
            if is_banned(message.author):
                await message.delete()
                await message.channel.send(
                    f"WARNING: User {message.author.name}#{message.author.discriminator} has been banned")
                return

            await command[k](config_dict[server_id], client, message)
            return

    # command with args
    for k in command_with_args.keys():
        if message.content.startswith(k + " "):
            # filter out blocked user
            if is_banned(message.author):
                await message.delete()
                await message.channel.send(
                    f"WARNING: User {message.author.name}#{message.author.discriminator} has been banned")
                return

            if len(message.content) < 1 + len(k):
                await message.channel.send("ERROR: Argument empty")
                continue
            text = message.content[1 + len(k):]
            await command_with_args[k](config_dict[server_id], client, message, text)
            return

    # tts channel
    if message.channel.name == TTS_CHANNEL:
        # filter out blocked user
        if is_banned(message.author):
            await message.delete()
            await message.channel.send(
                f"WARNING: User {message.author.name}#{message.author.discriminator} has been banned")
            return

        await say_text(config_dict[server_id], client, message, text=message.content)
        return
