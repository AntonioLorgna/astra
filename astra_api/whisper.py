from datetime import datetime
from pathlib import Path
# import stable_whisper 

class Whisper:
    loaded_models = list()

    @staticmethod
    def transcribe(file_path: Path, model: str):
        Whisper.loaded_models.append(model)
        return {
            "name": "такое крутое распознавание голоса",
            "text": "суперское просто",
            "filepath": str(file_path.resolve()),
            "model": model,
            "loaded_models": Whisper.loaded_models,
            "now": datetime.now().isoformat(),
        }