import discord

from handler.token import TOKEN
from handler.handler import handle_message

while True:
    try:
        client = discord.Client()

        @client.event
        async def on_message(message: discord.message.Message):
            await handle_message(client, message)

        client.run(TOKEN)
    except Exception as e:
        print(f"ERROR: {e}")
