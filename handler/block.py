import discord.member

BLOCK_FILENAME = "block.txt"


def is_blocked(author: discord.member.Member) -> bool:
    with open(BLOCK_FILENAME, "r") as f:
        blocked = set(map(lambda line: line[:-1] if line[-1] == "\n" else line, f.readlines()))
        return author.discriminator in blocked
