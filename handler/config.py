class Config:
    def __init__(self, server_id: int):
        self.server_id: int = server_id
        self.lang: str = "vi"
        self.tts_filename: str = f"temp_{server_id}.mp3"

    def __dict__(self):
        return {
            "lang": self.lang,
        }
