import discord

from context import Config, Context
from function import handle
from tok import TOKEN

while True:
    try:
        client = discord.Client()

        online = {}


        @client.event
        async def on_message(message: discord.message.Message):
            author: discord.member.Member = message.author
            # filter out self message
            if author == client.user:
                return
            # filter out bot message
            if author.bot:
                return
            if isinstance(message.channel, discord.DMChannel):
                await message.channel.send(
                    f"Hi {author.display_name}#{author.discriminator}, please add me to any server in order to use!",
                )
                return

            server_id = str(message.guild.id)
            if server_id not in online:
                online[server_id] = Config(server_id)
            await handle(Context(client, online[server_id], message))


        client.run(TOKEN)
    except Exception as e:
        print(f"ERROR: {e}")
