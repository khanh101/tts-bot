import os.path

import discord
import gtts.lang
from Levenshtein import jaro_winkler

from bot.util import __filter_banned_user, __parse_mention, __tts, __play_audio_file, __schedule_delete_message, \
    __resp_info, __resp_error, __resp_warning
from template import Context


async def say_text_default(ctx: Context):
    """say text in tts_channel"""
    if ctx.msg.channel.name == ctx.cfg.tts_channel:
        if await __filter_banned_user(ctx):
            return
        await say_text(ctx, ctx.msg.content)
        return


async def say_text(ctx: Context, text: str):
    """say text"""
    await __schedule_delete_message(ctx, ctx.msg)
    if await __filter_banned_user(ctx):
        return

    text = await __parse_mention(ctx, text)

    await __tts(ctx, text)
    await __play_audio_file(ctx, ctx.cfg.tts_path)


async def say_line(ctx: Context, text: str):
    """say line"""
    await __schedule_delete_message(ctx, ctx.msg)
    if await __filter_banned_user(ctx):
        return

    line_list = ctx.cfg.lines
    score_list = [jaro_winkler(line, text) for line in line_list]
    line = line_list[score_list.index(max(score_list))]

    line_path = os.path.join(ctx.cfg.line_dir, line) + ".mp3"

    await __resp_info(ctx, f"lining {line}")
    await __play_audio_file(ctx, line_path)


async def show_emoji(ctx: Context, text: str):
    """send emoji"""
    await __schedule_delete_message(ctx, ctx.msg)
    if await __filter_banned_user(ctx):
        return

    emoji_list = ctx.cfg.emojis
    score_list = [jaro_winkler(emoji, text) for emoji in emoji_list]
    emoji = emoji_list[score_list.index(max(score_list))]

    emoji_path = os.path.join(ctx.cfg.emoji_dir, emoji) + ".gif"
    await ctx.msg.channel.send(file=discord.File(emoji_path))


async def set_lang(ctx: Context, lang: str):
    """set language"""
    await __schedule_delete_message(ctx, ctx.msg)
    if await __filter_banned_user(ctx):
        return

    if lang not in gtts.lang.tts_langs():
        await __resp_error(ctx, f"language not available: {lang}")
        return

    ctx.cfg.lang = lang
    await __resp_warning(ctx, f"language was set to {lang}")


async def show_help(ctx: Context):
    """help"""
    await __schedule_delete_message(ctx, ctx.msg)
    if await __filter_banned_user(ctx):
        return

    bot_help = ""
    bot_help += "COMMAND\n"
    for key, cmd in ctx.bot.command_dict.items():
        bot_help += f"\t{key} : {cmd.__doc__}\n"
    bot_help += "COMMAND WITH ARGS\n"
    for key, cmd in ctx.bot.command_with_args_dict.items():
        bot_help += f"\t{key} <args> : {cmd.__doc__}\n"
    bot_help += "DEFAULT\n"
    if ctx.bot.default is not None:
        bot_help += f"\t{ctx.bot.default.__doc__}\n"
    else:
        bot_help += "\t<empty>\n"

    cfg_help = ""
    cfg_help += f"\ttts_channel : {ctx.cfg.tts_channel}\n"
    cfg_help += f"\tlang : {ctx.cfg.lang}\n"
    cfg_help += f"\tvoice_timeout : {ctx.cfg.voice_timeout}\n"
    cfg_help += f"\tresp_timeout : {ctx.cfg.resp_timeout}\n"
    cfg_help += f"\tban_list : {' '.join([discriminator for discriminator in ctx.cfg.ban_list])}\n"

    line_help = f"{' '.join(ctx.cfg.lines)}"

    lang_help = f"{' '.join(gtts.lang.tts_langs())}"

    text = f"""
    HELP
    {bot_help}
    CONFIG
    {cfg_help}
    LINE AVAILABLE
    {line_help}
    LANG AVAILABLE
    {lang_help}
    """

    await __resp_info(ctx, text)
