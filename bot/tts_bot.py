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


class TTSConfig(Config):
    class OfflineConfig:
        """
        OfflineConfig: a wrapper for a json file
        """

        def __init__(self, server_id: str, config_path: str, line_dir: str):
            self.server_id: str = server_id
            self.config_path: str = config_path
            self.line_dir: str = line_dir

        def __ensure(self):
            if not os.path.exists(self.config_path):
                self.__write({
                    "tts_channel": "tts-bot",
                    "lang": "vi",
                    "voice_timeout": 3600,
                    "resp_timeout": 30,
                    "ban_list": [],
                    "tts_path": f"tts_{self.server_id}.mp3",
                    "line_dir": self.line_dir,
                })

        def __getitem__(self, key: str) -> Any:
            return self.__read()[key]

        def __setitem__(self, key: str, value: Any):
            config = self.__read()
            config[key] = value
            self.__write(config)

        def __dict__(self) -> Dict[str, Any]:
            config = self.__read()
            return {
                "tts_channel": config["tts_channel"],
                "lang": config["lang"],
                "voice_timeout": config["voice_timeout"],
                "resp_timeout": config["resp_timeout"],
                "ban_list": config["ban_list"],
            }

        def __write(self, config: Dict[str, Any]):
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)

        def __read(self) -> Dict[str, Any]:
            self.__ensure()
            with open(self.config_path, "r") as f:
                return json.load(f)

    def __init__(self, server_id: str, config_path: str, line_dir: str):
        self.server_id: str = server_id
        self.offline: TTSConfig.OfflineConfig = TTSConfig.OfflineConfig(server_id, config_path, line_dir)
        self.last_voice_access: Optional[int] = None

    def lines(self) -> List[str]:
        return [".".join(filename.split('.')[:-1]) for filename in os.listdir(self.offline["line_dir"])]


tts_bot = Bot()


@default(tts_bot)
async def say_text_default(ctx: Context):
    """default action"""
    # tts channel
    bot, client, config, message = ctx
    if message.channel.name == config.offline["tts_channel"]:
        if await __filter_banned_user(ctx):
            return
        await say_text(ctx, message.content)
        return


@command_with_args(tts_bot, "!say")
async def say_text(ctx: Context, text: str):
    """!say <text>: say text or <text>: say text in tts channel"""
    if await __filter_banned_user(ctx):
        return
    bot, client, config, message = ctx
    words = text.split(" ")
    for i, w in enumerate(words):
        if w.startswith("<@!") and w.endswith(">"):
            words[i] = "mention"
    text = " ".join(words)
    await __tts(ctx, text)
    await __say_mp3file(ctx, config.offline["tts_path"])


@command_with_args(tts_bot, "!line")
async def say_line(ctx: Context, line: str):
    """!line <line>: say line"""
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
    """!lang <lang>: set language"""
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
    """!howto: help"""
    if await __filter_banned_user(ctx):
        return
    bot, client, config, message = ctx
    help_message = "HELP:\n"
    for f in bot.command_dict.values():
        help_message += f"\t{f.__doc__}\n"
    for f in bot.command_with_args_dict.values():
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
    await __schedule_delete_message(
        await message.channel.send(embed=discord.Embed(
            title="**INFO**",
            colour=0x00FF00,
            description=text,
        ).set_footer(text="INFO: intended use, need not to read")),
    )


async def __resp_warning(ctx: Context, text: str):
    bot, client, config, message = ctx
    await __schedule_delete_message(
        await message.channel.send(embed=discord.Embed(
            title="**WARNING**",
            colour=0x00FF00,
            description=text,
        ).set_footer(text="INFO: intended use, need not to read")),
    )


async def __resp_error(ctx: Context, text: str):
    bot, client, config, message = ctx
    await __schedule_delete_message(
        await message.channel.send(embed=discord.Embed(
            title="**ERROR**",
            colour=0xFF0000,
            description=text,
        ).set_footer(text="ERROR: not intended use, need to read")),
    )
