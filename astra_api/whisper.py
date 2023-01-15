from datetime import datetime
from pathlib import Path
import bson
# import stable_whisper 

class Whisper:
    loaded_models = list()

    @staticmethod
    def transcribe(file: bytes, model: str):
        Whisper.loaded_models.append(model)
        result = {
            "name": "супер имя",
            "text": "супер пупер мега крутой \nтекст"
        }

        return bson.dumps(result)