from bot.command import say_text_default, show_help, set_lang, say_text, say_line
from bot.config import TtsConfig
from template import Bot


def init_bot() -> Bot:
    bot = Bot()
    bot.set_default(say_text_default)
    bot.set_command("tts help", show_help)
    bot.set_command_with_args("tts lang", set_lang)
    bot.set_command_with_args("tts say", say_text)
    bot.set_command_with_args("tts line", say_line)
    return bot


def init_cfg(guild_id: str) -> TtsConfig:
    return TtsConfig(guild_id)
