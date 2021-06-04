from typing import Dict, Callable, Any

import discord

from bot_command import say_text, set_lang
from bot_token import TOKEN

client = discord.Client()

command: Dict[str, Callable[[discord.Client, discord.message.Message, Any], Any]] = {
    "!say": say_text,
    "!lang": set_lang,
}


@client.event
async def on_message(message: discord.message.Message):
    # filter out self message
    if message.author == client.user:
        return
    for k in command.keys():
        if message.content.startswith(k):
            text = message.content[1 + len(k):]
            await command[k](client, message, text)


client.run(TOKEN)