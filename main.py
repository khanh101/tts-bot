import discord

from handler.handler import handle_message
from handler.token import TOKEN

while True:
    try:
        client = discord.Client()


        @client.event
        async def on_message(message: discord.message.Message):
            await handle_message(client, message)


        client.run(TOKEN)
    except Exception as e:
        print(f"ERROR: {e}")
