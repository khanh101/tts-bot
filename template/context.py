from collections import namedtuple

Context = namedtuple("Context", ["bot", "cli", "cfg", "msg"])
"""
Context : contains all information to process a user message
"""
