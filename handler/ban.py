import discord.member

BAN_FILENAME = "ban.txt"


def is_banned(author: discord.member.Member) -> bool:
    with open(BAN_FILENAME, "r") as f:
        blocked = set(map(lambda line: line[:-1] if line[-1] == "\n" else line, f.readlines()))
        return author.discriminator in blocked
