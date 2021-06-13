from typing import Set

BLOCK_FILENAME = "block.txt"


def get_blocked_user() -> Set[str]:
    with open(BLOCK_FILENAME, "r") as f:
        return set(map(lambda line: line[:-1] if line[-1] == "\n" else line, f.readlines()))
