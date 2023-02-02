from enum import Enum
from dataclasses import dataclass

whisper_models_names = frozenset({
    'tiny',
    'base',
    'small',
    'medium',
    'large'
})

class WhisperModelsNames(str, Enum):
    tiny = 'tiny'
    base = 'base'
    small = 'small'
    medium = 'medium'
    large = 'large'


@dataclass
class WhisperModel():
    name: WhisperModelsNames
    parameters: int
    mem_usage: int
    relative_speed: int


class WhisperModels(Enum):
    tiny = WhisperModel(
        name='tiny',
        parameters=39,
        mem_usage=1<<30,
        relative_speed=32
    )
    base = WhisperModel(
        name='base',
        parameters=74,
        mem_usage=1<<30,
        relative_speed=16
    )
    small = WhisperModel(
        name='small',
        parameters=244,
        mem_usage=2 * 1<<30,
        relative_speed=6
    )
    medium = WhisperModel(
        name='medium',
        parameters=769,
        mem_usage=5 * 1<<30,
        relative_speed=2
    )
    large = WhisperModel(
        name='large',
        parameters=1550,
        mem_usage=10 * 1<<30,
        relative_speed=1
    )





