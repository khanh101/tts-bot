class Context:
    """
    Context : contains all information to process a user message
    """

    def __init__(self, bot, cli, cfg, req):
        self.bot = bot
        self.cli = cli
        self.cfg = cfg
        self.req = req
