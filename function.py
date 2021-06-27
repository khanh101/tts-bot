import asyncio
import os
import time
from enum import Enum
from typing import Optional

import discord
import gtts
from Levenshtein import jaro_winkler

from context import Context


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

    # command
    for k, f in command.items():
        if message.content == k:
            await __schedule_delete_message(ctx)
            if await __filter_banned_user(ctx):
                return
            await f(ctx)
            return
    # command with args
    for k, f in command_with_args.items():
        if message.content.startswith(k + " "):
            await __schedule_delete_message(ctx)
            if await __filter_banned_user(ctx):
                return
            if len(message.content) < 1 + len(k):
                await __log(ctx, LogType.ERROR, f"Argument empty")
                return
            text = message.content[1 + len(k):]
            await f(ctx, text)
            return

    # tts channel
    if message.channel.name == config.offline["tts_channel"]:
        if await __filter_banned_user(ctx):
            return
        await say_text(ctx, message.content)
        return


async def say_text(ctx: Context, text: str):
    """!say <text>: say text or <text>: say text in tts channel"""
    client, config, message = ctx
    words = text.split(" ")
    for i, w in enumerate(words):
        if w.startswith("<@!") and w.endswith(">"):
            words[i] = "mention"
    text = " ".join(words)
    await __tts(ctx, text)
    await __say_mp3file(ctx, config.offline["tts_path"])


async def say_line(ctx: Context, line: str):
    """!line <line>: say line"""
    client, config, message = ctx
    line_list = config.lines()
    score_list = [jaro_winkler(l, line) for l in line_list]
    line = line_list[score_list.index(max(score_list))]

    line_path = os.path.join(config.offline["line_dir"], line) + ".mp3"
    await __log(ctx, LogType.INFO, f"lining {line}")
    await __say_mp3file(ctx, line_path)


async def set_lang(ctx: Context, lang: str):
    """!lang <lang>: set language"""
    client, config, message = ctx
    try:
        gtts.gTTS("hello", lang=lang)
    except ValueError as e:
        await __log(ctx, LogType.ERROR, f"ERROR: {e}\nCurrent language: {config.offline['lang']}")
        return
    config.offline["lang"] = lang
    await __log(ctx, LogType.WARNING, f"Language was set into {lang}")


async def howto(ctx: Context):
    """!howto: help"""
    client, config, message = ctx
    help_message = "HELP:\n"
    for f in command.values():
        help_message += f"\t{f.__doc__}\n"
    for f in command_with_args.values():
        help_message += f"\t{f.__doc__}\n"
    help_message += f"CONFIG:\n"
    for k, v in config.offline.__dict__().items():
        help_message += f"\t{k}: {v}\n"
    help_message += "LINE AVAILABLE:\n"
    for line in config.lines():
        help_message += f"\t{line}"
    help_message += "\n"

    await __log(ctx, LogType.INFO, help_message)


async def __filter_banned_user(ctx: Context) -> bool:
    client, config, message = ctx
    if message.author.discriminator not in config.offline["ban_list"]:
        return False
    await __log(ctx, LogType.WARNING, f"{message.author.name}#{message.author.discriminator} has been banned")
    return True


async def __tts(ctx: Context, text: str):
    client, config, message = ctx
    gtts.gTTS(text=text, lang=config.offline["lang"]).save(config.offline["tts_path"])


async def __say_mp3file(ctx: Context, file_path: str):
    client, config, message = ctx
    # ensure author is in a voice channel
    author_voice_state: Optional[discord.VoiceState] = message.author.voice
    if author_voice_state is None:
        await __log(ctx, LogType.ERROR, f"{message.author} is not in any voice channel")
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


class LogType(Enum):
    INFO = ("INFO", 0x00FF00)
    WARNING = ("WARNING", 0xFFFF00)
    ERROR = ("ERROR", 0xFF0000)


async def __log(ctx: Context, logtype: LogType, text: str):
    """log"""
    client, config, message = ctx
    m = await message.channel.send(embed=discord.Embed(
        title=logtype.value[0],
        colour=logtype.value[1],
        description=text,
    ))
    await __schedule_delete_message(Context(client, config, m))


async def __schedule_disconnect_voice(ctx: Context, bot_voice_client: discord.VoiceClient):
    """schedule disconnecting voice after voice_timeout"""
    asyncio.ensure_future(__disconnect_voice_task(ctx, bot_voice_client))


async def __schedule_delete_message(ctx: Context):
    """schedule deleting message after log_timeout"""
    asyncio.ensure_future(__delete_message_task(ctx))


async def __delete_message_task(ctx: Context):
    """task: delete message after log_timeout"""
    client, config, message = ctx
    await asyncio.sleep(config.offline["log_timeout"])
    await message.delete()


async def __disconnect_voice_task(ctx: Context, bot_voice_client: discord.VoiceClient):
    """task: disconnect voice after voice_timeout"""
    client, config, message = ctx
    await asyncio.sleep(config.offline["voice_timeout"])
    elapsed = int(time.time()) - config.last_voice_access
    if bot_voice_client.is_connected() and elapsed >= config.offline["voice_timeout"] / 2:
        await bot_voice_client.disconnect()
        await __log(ctx, LogType.INFO, "Voice has been disconnected due to inactivity")


command = {
    "!howto": howto,
}
"""command"""
command_with_args = {
    "!say": say_text,
    "!lang": set_lang,
    "!line": say_line,
}
"""command with arguments"""
