import discord

from handler.token import TOKEN
from handler.handler import handle_message

client = discord.Client()

@client.event
async def on_message(message: discord.message.Message):
    await handle_message(client, message)

client.run(TOKEN)
