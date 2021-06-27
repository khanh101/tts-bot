import discord

from bot import Bot
from handle import handle
from tok import TOKEN

while True:
    try:
        client = discord.Client()

        online = {}


        @client.event
        async def on_message(message: discord.message.Message):
            server_id = str(message.guild.id)
            if server_id not in online:
                online[server_id] = Bot(client, server_id)
            await handle(online[server_id], message)


        client.run(TOKEN)
    except Exception as e:
        print(f"ERROR: {e}")
