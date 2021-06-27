import asyncio
import os
import time
from typing import Optional

import discord
import gtts
from Levenshtein import jaro_winkler

from bot import Bot


async def handle(bot: Bot, message: discord.Message):
    """handle a message with bot"""
    author: discord.member.Member = message.author
    # filter out bot message
    if author == bot.client.user:
        return
    # filter out bot message
    if author.bot:
        return

    # command
    for k, f in command.items():
        if message.content == k:
            await __schedule_delete_message(bot, message)
            if await __filter_banned_user(bot, message):
                return
            await f(bot, message)
            return
    # command with args
    for k, f in command_with_args.items():
        if message.content.startswith(k + " "):
            await __schedule_delete_message(bot, message)
            if await __filter_banned_user(bot, message):
                return
            if len(message.content) < 1 + len(k):
                await __log(bot, message, f"ERROR: Argument empty")
                return
            text = message.content[1 + len(k):]
            await f(bot, message, text)
            return

    # tts channel
    if message.channel.name == bot.config["tts_channel"]:
        if await __filter_banned_user(bot, message):
            return
        await say_text(bot, message, message.content)
        return


async def say_text(bot: Bot, message: discord.Message, text: str):
    """!say <text>: say text or <text>: say text in tts channel"""
    words = text.split(" ")
    for i, w in enumerate(words):
        if w.startswith("<@!") and w.endswith(">"):
            words[i] = "mention"
    text = " ".join(words)
    await __tts(bot, text)
    await __say_mp3file(bot, message, bot.config["tts_path"])


async def say_line(bot: Bot, message: discord.Message, line: str):
    """!line <line>: say line"""
    line_list = bot.get_lines()
    score_list = [jaro_winkler(l, line) for l in line_list]
    line = line_list[score_list.index(max(score_list))]

    line_path = os.path.join(bot.config["line_dir"], line) + ".mp3"
    await __say_mp3file(bot, message, line_path)
    await __log(bot, message, f"INFO: lining {line}")


async def set_lang(bot: Bot, message: discord.Message, lang: str):
    """!lang <lang>: set language"""
    try:
        gtts.gTTS("hello", lang=lang)
    except ValueError as e:
        await __log(bot, message, f"ERROR: {e}")
        await __log(bot, message, f"INFO: Current language: {bot.config['lang']}")
        return
    bot.config["lang"] = lang
    await __log(bot, message, f"WARNING: Language was set into {lang}")


async def howto(bot: Bot, message: discord.Message):
    """!howto: help"""
    help_message = "HELP:\n"
    for f in command.values():
        help_message += f"\t{f.__doc__}\n"
    for f in command_with_args.values():
        help_message += f"\t{f.__doc__}\n"
    help_message += f"CONFIG:\n"
    for k, v in bot.config.__dict__().items():
        help_message += f"\t{k}: {v}\n"
    help_message += "LINE AVAILABLE:\n"
    for line in bot.get_lines():
        help_message += f"\t{line}"
    help_message += "\n"

    await __log(bot, message, help_message)


async def __filter_banned_user(bot: Bot, message: discord.Message) -> bool:
    if message.author.discriminator not in bot.config["ban_list"]:
        return False
    await __log(
        bot,
        message,
        f"WARNING: {message.author.name}#{message.author.discriminator} has been banned",
    )
    return True


async def __tts(bot: Bot, text: str):
    gtts.gTTS(text=text, lang=bot.config["lang"]).save(bot.config["tts_path"])


async def __say_mp3file(bot: Bot, message: discord.Message, file_path: str):
    # ensure author is in a voice channel
    author_voice_state: Optional[discord.VoiceState] = message.author.voice
    if author_voice_state is None:
        await __log(bot, message, f"ERROR: {message.author} is not in any voice channel")
        return
    # ensure bot and author in the same voice channel
    author_voice_channel: discord.VoiceChannel = author_voice_state.channel
    bot_voice_client: discord.VoiceClient = discord.utils.get(bot.client.voice_clients, guild=message.guild)
    if bot_voice_client is None:
        await author_voice_channel.connect()
    elif bot_voice_client.channel != author_voice_channel:
        await bot_voice_client.disconnect()
        await author_voice_channel.connect()
    # play voice
    bot_voice_client: discord.VoiceClient = discord.utils.get(bot.client.voice_clients, guild=message.guild)
    bot_voice_client.stop()
    bot_voice_client.play(discord.FFmpegPCMAudio(source=file_path))

    # last access
    bot.last_voice_access = int(time.time())
    await __schedule_disconnect_voice(bot, message, bot_voice_client)


async def __log(bot: Bot, message: discord.Message, text: str):
    """log"""
    m = await message.channel.send(text)
    await __schedule_delete_message(bot, m)


async def __schedule_disconnect_voice(bot: Bot, message: discord.Message, bot_voice_client: discord.VoiceClient):
    """schedule disconnecting voice after voice_timeout"""
    asyncio.ensure_future(__disconnect_voice_task(bot, message, bot_voice_client))


async def __schedule_delete_message(bot: Bot, message: discord.Message):
    """schedule deleting message after log_timeout"""
    asyncio.ensure_future(__delete_message_task(bot, message))


async def __delete_message_task(bot: Bot, message: discord.Message):
    """task: delete message after log_timeout"""
    await asyncio.sleep(bot.config["log_timeout"])
    await message.delete()


async def __disconnect_voice_task(bot: Bot, message: discord.Message, bot_voice_client: discord.VoiceClient):
    """task: disconnect voice after voice_timeout"""
    await asyncio.sleep(bot.config["voice_timeout"])
    elapsed = int(time.time()) - bot.last_voice_access
    if bot_voice_client.is_connected() and elapsed >= bot.config["voice_timeout"] / 2:
        await bot_voice_client.disconnect()
        await __log(bot, message, "WARNING: Voice has been disconnected due to inactivity")


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
