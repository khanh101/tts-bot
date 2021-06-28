import asyncio
import os
import time
from typing import Optional

import discord
import gtts
import gtts.lang
from Levenshtein import jaro_winkler

from context import Context
from function import default, command_with_args, command, command_dict, command_with_args_dict
from utils import log, LogType


@default
async def say_text_default(ctx: Context):
    """default action"""
    # tts channel
    client, config, message = ctx
    if message.channel.name == config.offline["tts_channel"]:
        if await __filter_banned_user(ctx):
            return
        await say_text(ctx, message.content)
        return


@command_with_args("!say")
async def say_text(ctx: Context, text: str):
    """!say <text>: say text or <text>: say text in tts channel"""
    if await __filter_banned_user(ctx):
        return
    client, config, message = ctx
    words = text.split(" ")
    for i, w in enumerate(words):
        if w.startswith("<@!") and w.endswith(">"):
            words[i] = "mention"
    text = " ".join(words)
    await __tts(ctx, text)
    await __say_mp3file(ctx, config.offline["tts_path"])


@command_with_args("!line")
async def say_line(ctx: Context, line: str):
    """!line <line>: say line"""
    if await __filter_banned_user(ctx):
        return
    client, config, message = ctx
    line_list = config.lines()
    score_list = [jaro_winkler(l, line) for l in line_list]
    line = line_list[score_list.index(max(score_list))]

    line_path = os.path.join(config.offline["line_dir"], line) + ".mp3"
    await log(ctx, LogType.INFO, f"lining {line}")
    await __say_mp3file(ctx, line_path)


@command_with_args("!lang")
async def set_lang(ctx: Context, lang: str):
    """!lang <lang>: set language"""
    if await __filter_banned_user(ctx):
        return
    client, config, message = ctx
    try:
        gtts.gTTS("hello", lang=lang)
    except ValueError as e:
        await log(ctx, LogType.ERROR, f"{e}\nCurrent language: {config.offline['lang']}")
        return
    config.offline["lang"] = lang
    await log(ctx, LogType.WARNING, f"Language was set into {lang}")


@command("!howto")
async def howto(ctx: Context):
    """!howto: help"""
    if await __filter_banned_user(ctx):
        return
    client, config, message = ctx
    help_message = "HELP:\n"
    for f in command_dict.values():
        help_message += f"\t{f.__doc__}\n"
    for f in command_with_args_dict.values():
        help_message += f"\t{f.__doc__}\n"
    help_message += f"CONFIG:\n"
    for k, v in config.offline.__dict__().items():
        help_message += f"\t{k}: {v}\n"
    help_message += "LINE AVAILABLE:\n"
    for line in config.lines():
        help_message += f"\t{line}"
    help_message += "\n"
    help_message += "LANG AVAILABLE:\n"
    for lang in gtts.lang.tts_langs():
        help_message += f"\t{lang}"
    help_message += "\n"

    await log(ctx, LogType.INFO, help_message)


async def __filter_banned_user(ctx: Context) -> bool:
    client, config, message = ctx
    if message.author.discriminator not in config.offline["ban_list"]:
        return False
    await log(ctx, LogType.WARNING, f"{message.author.name}#{message.author.discriminator} has been banned")
    return True


async def __tts(ctx: Context, text: str):
    client, config, message = ctx
    gtts.gTTS(text=text, lang=config.offline["lang"]).save(config.offline["tts_path"])


async def __say_mp3file(ctx: Context, file_path: str):
    client, config, message = ctx
    # ensure author is in a voice channel
    author_voice_state: Optional[discord.VoiceState] = message.author.voice
    if author_voice_state is None:
        await log(ctx, LogType.ERROR, f"{message.author} is not in any voice channel")
        return
    # ensure config and author in the same voice channel
    author_voice_channel: discord.VoiceChannel = author_voice_state.channel
    bot_voice_client: discord.VoiceClient = discord.utils.get(client.voice_clients, guild=message.guild)
    if bot_voice_client is None:
        await author_voice_channel.connect()
    elif bot_voice_client.channel != author_voice_channel:
        await bot_voice_client.disconnect()
        await author_voice_channel.connect()
    # play voice
    bot_voice_client: discord.VoiceClient = discord.utils.get(client.voice_clients, guild=message.guild)
    bot_voice_client.stop()
    bot_voice_client.play(discord.FFmpegPCMAudio(source=file_path))

    # last access
    config.last_voice_access = int(time.time())
    await __schedule_disconnect_voice(ctx, bot_voice_client)


async def __schedule_disconnect_voice(ctx: Context, bot_voice_client: discord.VoiceClient):
    """schedule disconnecting voice after voice_timeout"""

    async def __disconnect_voice_task():
        """task: disconnect voice after voice_timeout"""
        client, config, message = ctx
        await asyncio.sleep(config.offline["voice_timeout"])
        elapsed = int(time.time()) - config.last_voice_access
        if bot_voice_client.is_connected() and elapsed >= config.offline["voice_timeout"] / 2:
            await bot_voice_client.disconnect()
            await log(ctx, LogType.INFO, "Voice has been disconnected due to inactivity")

    asyncio.ensure_future(__disconnect_voice_task())
