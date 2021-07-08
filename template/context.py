class Context:
    """
    Context : contains all information to process a user message
    """

    def __init__(self, bot, cli, cfg, msg):
        self.bot = bot
        self.cli = cli
        self.cfg = cfg
        self.msg = msg
