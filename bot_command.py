from typing import Optional

import discord
import gtts

lang = "en"


async def tts(text: str, filename: str = "tts.mp3"):
    gtts.gTTS(text=text, lang=lang).save(filename)


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
    # ensure author is in a voice channel
    author_voice_state: Optional[discord.member.VoiceState] = message.author.voice
    if author_voice_state is None:
        await message.channel.send("ERROR: Author is not current in any voice channel!")
        return
    # async: tts
    tts_done = tts(text=text)
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
    try:
        await tts_done
    except AssertionError as e:
        await message.channel.send(f"ERROR: {e}")
        return
    bot_voice_client.play(discord.FFmpegPCMAudio("tts.mp3"))
    # await message.channel.send(f"INFO: Text was send to voice channel {author_voice_channel}: {text}")
