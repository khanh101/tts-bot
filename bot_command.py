import os
from typing import Optional

import discord
import gtts

LANG = "vi"
TTS_FILENAME = "tts.mp3"
SPECIAL_FOLDER = "special"
TTS_CHANNEL = "tts-bot"


async def _tts(text: str, filename: str):
    gtts.gTTS(text=text, lang=LANG).save(filename)


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
    global LANG
    try:
        gtts.gTTS("hello", lang=new_lang)
    except ValueError as e:
        await message.channel.send(f"ERROR: {e}")
        await message.channel.send(f"INFO: Current language: {LANG}")
        return
    LANG = new_lang
    await message.channel.send(f"WARNING: Language was set into {LANG}")


async def set_tts_channel(client: discord.Client, message: discord.message.Message, new_text_channel: str):
    global TTS_CHANNEL
    TTS_CHANNEL = new_text_channel
    await message.channel.send(f"INFO: Text channel was set into {TTS_CHANNEL}")

def get_tts_channel() -> str:
    global TTS_CHANNEL
    return TTS_CHANNEL


async def say_text(client: discord.Client, message: discord.message.Message, text: str):
    await _tts(text=text, filename=TTS_FILENAME)
    await _say_mp3file(client, message, TTS_FILENAME)


async def say_special(client: discord.Client, message: discord.message.Message, name: str):
    filename = os.path.join(SPECIAL_FOLDER, name) + ".mp3"
    if not os.path.exists(filename):
        await message.channel.send(f"ERROR: Special not found: {name}")
        return
    await _say_mp3file(client, message, filename)


async def howto(client: discord.Client, message: discord.message.Message):
    help_message = "HOW TO:\n"
    help_message += "\t !say <text> : say text\n"
    help_message += "\t !lang <lang> : change language\n"
    help_message += "\t !special <special> : say special\n"
    help_message += f"\t <text>: say text if text in tts channel: {TTS_CHANNEL}\n"
    help_message += "\t !tts_channel <channel>: set tts channel\n"
    help_message += "SPECIAL LIST:\n"
    for filename in os.listdir(SPECIAL_FOLDER):
        help_message += f"\t{'.'.join(filename.split('.')[:-1])}"

    await message.channel.send(help_message)
