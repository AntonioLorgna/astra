from collections import OrderedDict
from dataclasses import dataclass


class WhisperModels:
    @dataclass
    class WhisperModelInfo:
        name: str
        parameters: int
        mem_usage: int
        relative_speed: int

    _DATA = {
        "tiny": WhisperModelInfo(
            name="tiny", parameters=39, mem_usage=1 << 30, relative_speed=32
        ),
        "base": WhisperModelInfo(
            name="base", parameters=74, mem_usage=1 << 30, relative_speed=16
        ),
        "small": WhisperModelInfo(
            name="small", parameters=244, mem_usage=2 * 1 << 30, relative_speed=6
        ),
        "medium": WhisperModelInfo(
            name="medium", parameters=769, mem_usage=5 * 1 << 30, relative_speed=2
        ),
        "large": WhisperModelInfo(
            name="large", parameters=1550, mem_usage=10 * 1 << 30, relative_speed=1
        ),
    }

    def get_params(modelname: str):
        model = WhisperModels._DATA.get(modelname)
        if model is None:
            return None
        return model.parameters

    def list_models():
        return list(WhisperModels._DATA.keys())

    def exist(modelname: str):
        return WhisperModels._DATA.get(modelname) is not None

    def is_more_accurate(modelname_a: str, modelname_b: str, or_same=False):
        model_a = WhisperModels._DATA.get(modelname_a)
        if model_a is None:
            return True
        model_b = WhisperModels._DATA.get(modelname_b)
        if model_b is None:
            return False

        if or_same:
            return model_a.parameters <= model_b.parameters

        return model_a.parameters < model_b.parameters

    def get_more_accurate(modelname: str, or_same=False, sort_desc=True):
        model = WhisperModels._DATA.get(modelname)
        ordered = OrderedDict(
            sorted(
                WhisperModels._DATA.items(),
                key=lambda m: m[1].parameters,
                reverse=sort_desc,
            )
        )
        return [
            n
            for n, m in ordered.items()
            if m.parameters > model.parameters
            or (or_same and m.parameters == model.parameters)
        ]

    def mem_usage(modelname: str):
        model = WhisperModels._DATA.get(modelname)
        if model is None:
            raise Exception(f"Whisper model with name '{modelname}' not found!")
        return model.mem_usage
