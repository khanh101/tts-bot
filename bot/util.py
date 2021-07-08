import asyncio
import time
from typing import Optional

import discord
import gtts
from discord import Message

from template import Context


async def __play_audio_file(ctx: Context, path: str):
    # ensure author in a voice channel
    author_voice_state: Optional[discord.VoiceState] = ctx.req.author.voice
    if author_voice_state is None:
        await __resp_error(ctx, f"{ctx.req.author.name}#{ctx.req.author.discriminator} is not in any voice channel")
        return
    # ensure author and bot in the same voice channel
    bot_voice_client: discord.VoiceClient = discord.utils.get(ctx.cli.voice_clients, guild=ctx.req.guild)
    if bot_voice_client is None:
        await author_voice_state.channel.connect()
    elif bot_voice_client.channel != author_voice_state.channel:
        await bot_voice_client.disconnect()
        await author_voice_state.channel.connect()

    # play audio file
    bot_voice_client: discord.VoiceClient = discord.utils.get(ctx.cli.voice_clients, guild=ctx.req.guild)
    bot_voice_client.stop()
    bot_voice_client.play(discord.FFmpegPCMAudio(source=path))

    # last voice access
    ctx.cfg.last_voice_access = int(time.time())
    await __schedule_disconnect_voice(ctx, bot_voice_client)


async def __tts(ctx: Context, text: str):
    gtts.gTTS(text=text, lang=ctx.cfg.lang).save(ctx.cfg.tts_path)


async def __parse_mention(ctx: Context, text: str) -> str:
    text = text.replace("!", "")
    for user in ctx.req.mentions:
        if user.nick is not None:
            nick = user.nick
        else:
            nick = user.name
        mention = user.mention
        mention = mention.replace("!", "")
        text = text.replace(mention, nick)
    return text


async def __filter_banned_user(ctx: Context) -> bool:
    if ctx.req.author.discriminator not in ctx.cfg.ban_list:
        return False
    await __resp_warning(ctx, f"{ctx.req.author.name}#{ctx.req.author.discriminator} has been banned")
    return True


async def __resp_info(ctx: Context, text: str):
    await __schedule_delete_message(ctx, await ctx.req.channel.send(embed=discord.Embed(
        title="**INFO**",
        colour=0x00FF00,
        description=text,
    ).set_footer(text="ERROR: intended use, need not to read")))


async def __resp_warning(ctx: Context, text: str):
    await __schedule_delete_message(ctx, await ctx.req.channel.send(embed=discord.Embed(
        title="**WARNING**",
        colour=0xFFFF00,
        description=text,
    ).set_footer(text="ERROR: intended use, need to read")))


async def __resp_error(ctx: Context, text: str):
    await __schedule_delete_message(ctx, await ctx.req.channel.send(embed=discord.Embed(
        title="**ERROR**",
        colour=0xFF0000,
        description=text,
    ).set_footer(text="ERROR: not intended use, need to read")))


async def __schedule_disconnect_voice(ctx: Context, voice_client: discord.VoiceClient):
    """schedule disconnecting voice after voice_timeout"""

    async def __disconnect_voice_task():
        """task: disconnect voice after voice_timeout"""
        await asyncio.sleep(ctx.cfg.voice_timeout)
        elapsed = int(time.time()) - ctx.cfg.last_voice_access
        if voice_client.is_connected() and elapsed >= ctx.cfg.voice_timeout:
            await voice_client.disconnect()
            await __resp_info(ctx, "voice has been disconnected due to inactivity")

    asyncio.ensure_future(__disconnect_voice_task())


async def __schedule_delete_message(ctx: Context, msg: Message):
    """schedule deleting message after resp_timeout"""

    async def __delete_message_task():
        """task: delete message after resp_timeout"""
        await asyncio.sleep(ctx.cfg.resp_timeout)
        try:
            await msg.delete()
        except discord.errors.NotFound:
            pass

    asyncio.ensure_future(__delete_message_task())
