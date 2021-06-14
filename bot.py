import asyncio
import json
import os
import time
from typing import Dict, Any, Optional

import discord
import gtts


class Config:
    def __init__(self, server_id: str):
        self.server_id: str = server_id

    def __ensure(self):
        if not os.path.exists("cfg"):
            os.mkdir("cfg")
        if not os.path.exists("tts"):
            os.mkdir("tts")
        if not os.path.exists("line"):
            os.mkdir("line")
        if not os.path.exists(self.__get_config_path()):
            self.__write({
                "lang": "vi",
                "tts_path": os.path.join("tts", f"tts_{self.server_id}.mp3"),
                "voice_timeout": 300,
                "log_timeout": 30,
                "ban_list": [],
                "line_dir": "line",
                "tts_channel": "tts-bot"
            })

    def __getitem__(self, key: str) -> Any:
        config = self.__read()
        return config.get(key, None)

    def __setitem__(self, key: str, value: Any):
        config = self.__read()
        config[key] = value
        self.__write(config)

    def __dict__(self) -> Dict[str, Any]:
        return self.__read()

    def __get_config_path(self) -> str:
        return os.path.join("cfg", f"cfg_{self.server_id}.json")

    def __write(self, config: Dict[str, Any]):
        with open(self.__get_config_path(), "w") as f:
            json.dump(config, f, indent=4)

    def __read(self) -> Dict[str, Any]:
        self.__ensure()
        with open(self.__get_config_path(), "r") as f:
            return json.load(f)


class Bot:
    def __init__(self, client: discord.Client, server_id: str):
        self.client: discord.Client = client
        self.server_id: str = server_id
        self.config: Config = Config(server_id)
        self.last_access: Optional[int] = None
        self.gonna_disconnect: bool = False
        self.command = {
            "!howto": self.howto,
        }
        self.command_with_args = {
            "!say": self.say_text,
            "!lang": self.set_lang,
            "!line": self.say_line,
        }


    async def handle(self, message: discord.Message):
        author: discord.member.Member = message.author
        # filter out self message
        if author == self.client.user:
            return
        # filter out bot message
        if author.bot:
            return

        content: str = message.content
        # command
        for k, f in self.command.items():
            if message.content == k:
                if message.author.discriminator in self.config["ban_list"]:
                    await message.delete()
                    await self.__log(
                        message,
                        f"WARNING: {message.author.name}#{message.author.discriminator} has been banned",
                    )
                    return

                await f(message)
                return
        # command with args
        for k, f in self.command_with_args.items():
            if message.content.startswith(k + " "):
                if message.author.discriminator in self.config["ban_list"]:
                    await message.delete()
                    await self.__log(
                        message,
                        f"WARNING: {message.author.name}#{message.author.discriminator} has been banned",
                    )
                    return
                if len(message.content) < 1 + len(k):
                    await self.__log(message, f"ERROR: Argument empty")
                    return
                text = message.content[1 + len(k):]
                await f(message, text)
                return

        # tts channel
        if message.channel.name == self.config["tts_channel"]:
            if message.author.discriminator in self.config["ban_list"]:
                await message.delete()
                await self.__log(
                    message,
                    f"WARNING: {message.author.name}#{message.author.discriminator} has been banned",
                )
                return
            await self.say_text(message, message.content)
            return

    async def say_text(self, message: discord.Message, text: str):
        """!say <text>: say text or <text>: say text in tts channel"""
        await self.__tts(text)
        await self.__say_mp3file(message, self.config["tts_path"])

    async def say_line(self, message: discord.Message, line: str):
        """!line <line>: say line"""
        line_path = os.path.join(self.config["line_dir"], line) + ".mp3"
        if not os.path.exists(line_path):
            await self.__log(message, f"ERROR: Line not found: {line}")
            return
        await self.__say_mp3file(message, line_path)

    async def set_lang(self, message: discord.Message, lang: str):
        """!lang <lang>: set language"""
        try:
            gtts.gTTS("hello", lang=lang)
        except ValueError as e:
            await self.__log(message, f"ERROR: {e}")
            await self.__log(message, "INFO: Current language: {self.config['lang']}")
            return
        self.config["lang"] = lang
        await self.__log(message, f"WARNING: Language was set into {lang}")

    async def howto(self, message: discord.Message):
        """!howto: help"""
        help_message = "HELP: https://github.com/khanhcsc/tts-bot\n"
        for f in self.command.values():
            help_message += f"\t{f.__doc__}\n"
        for f in self.command_with_args.values():
            help_message += f"\t{f.__doc__}\n"
        help_message += f"CONFIG:\n"
        for k, v in self.config.__dict__().items():
            help_message += f"\t{k}: {v}\n"
        help_message += "LINE AVAILABLE:\n"
        for filename in os.listdir(self.config["line_dir"]):
            help_message += f"\t{'.'.join(filename.split('.')[:-1])}"

        await self.__log(message, help_message)

    async def __log(self, message: discord.Message, text: str):
        m = await message.channel.send(text)
        await asyncio.sleep(self.config["log_timeout"])
        await m.delete()

    async def __tts(self, text: str):
        gtts.gTTS(text=text, lang=self.config["lang"]).save(self.config["tts_path"])

    async def __say_mp3file(self, message: discord.Message, file_path: str):
        # ensure author is in a voice channel
        author_voice_state: Optional[discord.VoiceState] = message.author.voice
        if author_voice_state is None:
            await self.__log(message, f"ERROR: {message.author} is not in any voice channel")
            return
        # ensure bot and author in the same voice channel
        author_voice_channel: discord.VoiceChannel = author_voice_state.channel
        bot_voice_client: discord.VoiceClient = discord.utils.get(self.client.voice_clients, guild=message.guild)
        if bot_voice_client is None:
            await author_voice_channel.connect()
        elif bot_voice_client.channel != author_voice_channel:
            await bot_voice_client.disconnect()
            await author_voice_channel.connect()
        # play voice
        bot_voice_client: discord.VoiceClient = discord.utils.get(self.client.voice_clients, guild=message.guild)
        bot_voice_client.stop()
        bot_voice_client.play(discord.FFmpegPCMAudio(source=file_path))

        # last access
        self.last_access = int(time.time())
        if self.gonna_disconnect:
            return
        self.gonna_disconnect = True
        await asyncio.sleep(self.config["voice_timeout"])
        if int(time.time()) - self.last_access >= self.config["voice_timeout"] / 2:
            self.gonna_disconnect = False
            await bot_voice_client.disconnect()
            await self.__log(message, "WARNING: Voice has been disconnected due to inactivity")
