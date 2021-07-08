from template.context import Context


async def handle(ctx: Context):
    """
    handle : handles context
    """
    # filter out self message
    if ctx.cli.user == ctx.msg.author:
        return
    # filter out bot message
    if ctx.msg.author.bot:
        return

    # command : exact match
    if ctx.msg.content in ctx.bot.command_dict:
        await ctx.bot.command_dict[ctx.msg.content](ctx)
        return

    # command with args : match "<key><space><something else>"
    for key in ctx.bot.command_with_args_dict:
        if ctx.msg.content.startswith(key + " "):
            args = ctx.msg.content[len(key + " "):]
            await ctx.bot.command_with_args_dict[key](ctx, args)
            return

    # default :
    if ctx.bot.default is not None:
        await ctx.bot.default(ctx)
        return
