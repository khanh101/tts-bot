import asyncio
import os
import time
from typing import Optional

import discord
import gtts

from handler.config import Config

# constant
LINE_FOLDERNAME = "line"
TTS_CHANNEL = "tts-bot"
TIMEOUT = 300  # 5 minutes


async def _tts(text: str, filename: str, lang: str):
    gtts.gTTS(text=text, lang=lang).save(filename)


last_access = {}


async def _say_mp3file(config: Config, client: discord.Client, message: discord.message.Message, filename: str):
    # ensure author is in a voice channel
    author_voice_state: Optional[discord.member.VoiceState] = message.author.voice
    if author_voice_state is None:
        await message.channel.send(f"ERROR: {message.author} is not current in any voice channel!")
        return
    # get author voice channel
    author_voice_channel: discord.channel.VoiceChannel = author_voice_state.channel
    # get bot voice channel
    bot_voice_client: discord.voice_client.VoiceClient = discord.utils.get(client.voice_clients, guild=message.guild)
    if bot_voice_client is None:
        await author_voice_channel.connect()
    elif bot_voice_client.channel != author_voice_channel:
        await bot_voice_client.disconnect()
        await author_voice_channel.connect()

    bot_voice_client = discord.utils.get(client.voice_clients, guild=message.guild)
    bot_voice_client.stop()
    bot_voice_client.play(discord.FFmpegPCMAudio(source=filename))

    # last access
    server_id = int(message.guild.id)
    last_access[server_id] = int(time.time()), bot_voice_client
    await asyncio.sleep(TIMEOUT)
    # auto disconnect
    if server_id in last_access and int(time.time()) - last_access[server_id][0] >= TIMEOUT / 2:
        await last_access[server_id][1].disconnect()
        del last_access[server_id]


async def set_lang(config: Config, client: discord.Client, message: discord.message.Message, lang: str):
    """!lang <lang>: set language"""
    try:
        gtts.gTTS("hello", lang=lang)
    except ValueError as e:
        await message.channel.send(f"ERROR: {e}")
        await message.channel.send(f"INFO: Current language: {config.lang}")
        return
    config.lang = lang
    await message.channel.send(f"WARNING: Language was set into {config.lang}")


async def say_text(config: Config, client: discord.Client, message: discord.message.Message, text: str):
    """!say <text>: say text"""
    await _tts(text=text, filename=config.tts_filename, lang=config.lang)
    await _say_mp3file(config, client, message, config.tts_filename)


async def say_line(config: Config, client: discord.Client, message: discord.message.Message, name: str):
    """!line <code>: say line"""
    filename = os.path.join(LINE_FOLDERNAME, name) + ".mp3"
    if not os.path.exists(filename):
        await message.channel.send(f"ERROR: Line not found: {name}")
        return
    await _say_mp3file(config, client, message, filename)
