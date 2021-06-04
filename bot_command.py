import os
from typing import Optional

import discord
import gtts

lang = "vi"


async def _tts(text: str, filename: str):
    gtts.gTTS(text=text, lang=lang).save(filename)


async def _say_mp3file(client: discord.Client, message: discord.message.Message, filename: str):
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


async def set_lang(client: discord.Client, message: discord.message.Message, new_lang: str):
    global lang
    try:
        gtts.gTTS("hello", lang=new_lang)
    except ValueError as e:
        await message.channel.send(f"ERROR: {e}")
        await message.channel.send(f"INFO: Current language: {lang}")
        return
    lang = new_lang
    await message.channel.send(f"WARNING: Language was set into {lang}")


async def say_text(client: discord.Client, message: discord.message.Message, text: str):
    await _tts(text=text, filename=".tts.mp3")
    await _say_mp3file(client, message, ".tts.mp3")


async def say_special(client: discord.Client, message: discord.message.Message, name: str):
    filename = f"{name}.mp3"
    if not os.path.exists(filename):
        await message.channel.send(f"ERROR: Special not found: {name}")
        return
    await _say_mp3file(client, message, filename)
