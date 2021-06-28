import asyncio
from enum import Enum

import discord

from context import Context


async def schedule_delete_message(ctx: Context):
    """schedule deleting message after log_timeout"""

    async def __delete_message_task():
        """task: delete message after log_timeout"""
        client, config, message = ctx
        await asyncio.sleep(config.offline["log_timeout"])
        try:
            await message.delete()
        except discord.errors.NotFound:
            pass

    asyncio.ensure_future(__delete_message_task())


class LogType(Enum):
    INFO = ("**INFO**", "intended use, need not to read", 0x00FF00)
    WARNING = ("**WARNING**", "intended use, need to read", 0xFFFF00)
    ERROR = ("**ERROR**", "not intended use, need to read", 0xFF0000)


async def log(ctx: Context, logtype: LogType, text: str):
    """log"""
    client, config, message = ctx
    m = await message.channel.send(embed=discord.Embed(
        title=logtype.value[0],
        colour=logtype.value[2],
        description=text,
    ).set_footer(text=logtype.value[1]))
    await schedule_delete_message(Context(client, config, m))
