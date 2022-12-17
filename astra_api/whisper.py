from datetime import datetime
from pathlib import Path
# import stable_whisper 

class Whisper:
    loaded_models = list()

    @staticmethod
    def transcribe(file_path: Path, model: str):
        Whisper.loaded_models.append(model)
        return "такое крутое распознавание голоса"