import os
from typing import Dict, Callable, Any

import discord

from bot_command import say_text, set_lang, say_special, howto, TTS_CHANNEL, set_tts_channel, get_tts_channel
from bot_token import TOKEN

client = discord.Client()

command_with_args: Dict[str, Callable[[discord.Client, discord.message.Message, Any], Any]] = {
    "!say": say_text,
    "!lang": set_lang,
    "!tts_channel": set_tts_channel,
    "!special": say_special,
}

command: Dict[str, Callable[[discord.Client, discord.message.Message], Any]] = {
    "!howto": howto,
}

@client.event
async def on_message(message: discord.message.Message):
    # filter out self message
    if message.author == client.user:
        return

    # command
    for k in command.keys():
        if message.content.startswith(k):
            await command[k](client, message)
            return

    # command with args
    for k in command_with_args.keys():
        if message.content.startswith(k):
            if len(message.content) < 1 + len(k):
                await message.channel.send("ERROR: Argument empty")
                continue
            text = message.content[1 + len(k):]
            await command_with_args[k](client, message, text)
            return

    if message.channel.name == get_tts_channel():
        await say_text(client, message, text=message.content)
        return


client.run(TOKEN)
