import asyncio
import json
import os
import time
from typing import Optional, Any, Dict, List

import discord
import gtts
import gtts.lang
from Levenshtein import jaro_winkler

from bot.template import Config, Bot, default, Context, command_with_args, command
from bot.utils import JsonObject


class TTSConfig(Config):
    def __init__(self, server_id: str, config_path: str, line_dir: str):
        self.server_id: str = server_id
        self.offline: JsonObject = JsonObject(
            config_path=config_path,
            default={
                "tts_channel": "tts-bot",
                "lang": "vi",
                "voice_timeout": 3600,
                "resp_timeout": 30,
                "ban_list": [],
                "tts_path": f"tts_{server_id}.mp3",
                "line_dir": line_dir,
            },
        )
        self.last_voice_access: Optional[int] = None

    def lines(self) -> List[str]:
        return [".".join(filename.split('.')[:-1]) for filename in os.listdir(self.offline["line_dir"])]


tts_bot = Bot()


@default(tts_bot)
async def say_text_default(ctx: Context):
    """say text in tts_channel"""
    # tts channel
    bot, client, config, message = ctx
    if message.channel.name == config.offline["tts_channel"]:
        if await __filter_banned_user(ctx):
            return
        await say_text(ctx, message.content)
        return


@command_with_args(tts_bot, "!say")
async def say_text(ctx: Context, text: str):
    """say text"""
    if await __filter_banned_user(ctx):
        return
    bot, client, config, message = ctx

    # replace mention by nickname
    # remove all !
    text = text.replace("!", "")
    for user in message.mentions:
        if user.nick is not None:
            nick = user.nick
        else:
            nick = user.name
        mention = user.mention
        mention = mention.replace("!", "")
        text = text.replace(mention, nick)

    await __tts(ctx, text)
    await __say_mp3file(ctx, config.offline["tts_path"])


@command_with_args(tts_bot, "!line")
async def say_line(ctx: Context, line: str):
    """say line"""
    await __schedule_delete_message(ctx)
    if await __filter_banned_user(ctx):
        return
    bot, client, config, message = ctx
    line_list = config.lines()
    score_list = [jaro_winkler(l, line) for l in line_list]
    line = line_list[score_list.index(max(score_list))]

    line_path = os.path.join(config.offline["line_dir"], line) + ".mp3"
    await __resp_info(ctx, f"lining {line}")
    await __say_mp3file(ctx, line_path)


@command_with_args(tts_bot, "!lang")
async def set_lang(ctx: Context, lang: str):
    """set language"""
    await __schedule_delete_message(ctx)
    if await __filter_banned_user(ctx):
        return
    bot, client, config, message = ctx
    try:
        gtts.gTTS("hello", lang=lang)
    except ValueError as e:
        await __resp_error(ctx, f"{e}\nCurrent language: {config.offline['lang']}")
        return
    config.offline["lang"] = lang
    await __resp_warning(ctx, f"Language was set into {lang}")


@command(tts_bot, "!howto")
async def howto(ctx: Context):
    """help"""
    await __schedule_delete_message(ctx)
    if await __filter_banned_user(ctx):
        return
    bot, client, config, message = ctx
    bot_help = bot.__repr__()
    config_help = "\n".join([f"{k} : {v}" for k, v in config.offline.items()])
    line_available = " ".join(config.lines())
    lang_available = " ".join(gtts.lang.tts_langs())

    help_message = f"""
    HELP
    {bot_help}
    CONFIG
    {config_help}
    LINE AVAILABLE
    {line_available}
    LANG AVAILABLE
    {lang_available}
    """

    await __resp_info(ctx, help_message)


async def __filter_banned_user(ctx: Context) -> bool:
    bot, client, config, message = ctx
    if message.author.discriminator not in config.offline["ban_list"]:
        return False
    await __resp_warning(ctx, f"{message.author.name}#{message.author.discriminator} has been banned")
    return True


async def __tts(ctx: Context, text: str):
    bot, client, config, message = ctx
    gtts.gTTS(text=text, lang=config.offline["lang"]).save(config.offline["tts_path"])


async def __say_mp3file(ctx: Context, file_path: str):
    bot, client, config, message = ctx
    # ensure author is in a voice channel
    author_voice_state: Optional[discord.VoiceState] = message.author.voice
    if author_voice_state is None:
        await __resp_error(ctx, f"{message.author} is not in any voice channel")
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
        bot, client, config, message = ctx
        await asyncio.sleep(config.offline["voice_timeout"])
        elapsed = int(time.time()) - config.last_voice_access
        if bot_voice_client.is_connected() and elapsed >= config.offline["voice_timeout"] / 2:
            await bot_voice_client.disconnect()
            await __resp_info(ctx, "Voice has been disconnected due to inactivity")

    asyncio.ensure_future(__disconnect_voice_task())


async def __schedule_delete_message(ctx: Context):
    """schedule deleting message after resp_timeout"""
    bot, client, config, message = ctx

    async def __delete_message_task():
        """task: delete message after resp_timeout"""
        await asyncio.sleep(config.offline["resp_timeout"])
        try:
            await message.delete()
        except discord.errors.NotFound:
            pass

    asyncio.ensure_future(__delete_message_task())


async def __resp_info(ctx: Context, text: str):
    bot, client, config, message = ctx
    await __schedule_delete_message(Context(
        bot, client, config,
        await message.channel.send(embed=discord.Embed(
            title="**INFO**",
            colour=0x00FF00,
            description=text,
        ).set_footer(text="INFO: intended use, need not to read")),
    ))


async def __resp_warning(ctx: Context, text: str):
    bot, client, config, message = ctx
    await __schedule_delete_message(Context(
        bot, client, config,
        await message.channel.send(embed=discord.Embed(
            title="**WARNING**",
            colour=0xFFFF00,
            description=text,
        ).set_footer(text="WARNING: intended use, need not to read")),
    ))


async def __resp_error(ctx: Context, text: str):
    bot, client, config, message = ctx
    await __schedule_delete_message(Context(
        bot, client, config,
        await message.channel.send(embed=discord.Embed(
            title="**ERROR**",
            colour=0xFF0000,
            description=text,
        ).set_footer(text="ERROR: not intended use, need not to read")),
    ))
