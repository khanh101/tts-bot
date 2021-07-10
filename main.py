import os
import sys

import discord

from bot import init_cfg, init_bot
from template import handle, Context

DEBUG = True

TOKEN = ""


def init():
    if len(sys.argv) <= 1:
        sys.exit("start template: python main.py <TOKEN>")

    global TOKEN
    TOKEN = sys.argv[1]


if __name__ == "__main__":
    init()

    # create config and line dir
    if not os.path.exists("cfg"):
        os.mkdir("cfg")
    if not os.path.exists("line"):
        os.mkdir("line")
    if not os.path.exists("emoji"):
        os.mkdir("emoji")

    while True:
        try:
            cli = discord.Client()

            tts_bot = init_bot()
            online = {}


            async def helper(msg: discord.Message):
                if DEBUG and msg.channel.name != "test":
                    # in debug mode, only serve messages from test
                    return

                if not DEBUG and msg.channel.name == "test":
                    # not in debug mode, skip messages from test
                    return

                guild_id = str(msg.guild.id)
                if guild_id not in online:
                    online[guild_id] = init_cfg(guild_id)

                await handle(Context(tts_bot, cli, online[guild_id], msg))


            @cli.event
            async def on_message(msg: discord.Message):
                await helper(msg)


            @cli.event
            async def on_message_edit(before: discord.Message, after: discord.Message):
                await helper(after)


            cli.run(TOKEN)
        except Exception as e:
            print(f"ERROR: {e}")
