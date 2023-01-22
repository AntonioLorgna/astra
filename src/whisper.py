from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from sys import stdout
from typing import Any, Dict, List, Set
from stable_whisper import load_model
from stable_whisper.stabilization import tighten_timestamps
import torch
from whisper import _download, _MODELS
from datetime import timedelta, datetime
from pathlib import Path
import re, itertools, os
import calendar
import logging
import src.utils as utils
import src.whisper_models as whisper_models
logger = logging.getLogger(__name__)

_ru_month_starts = [
    'январ',
    'феврал',
    'март',
    'апрел',
    'ма',
    'июн',
    'июл',
    'август',
    'сентябр',
    'октябр',
    'ноябр',
    'декабр',
]

device_type = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device '{device_type}' for ML.")

@dataclass
class _LoadedModel:
    model_ml: Any
    model_info: whisper_models.WhisperModel

class Whisper(metaclass=utils.Singleton):
    def __init__(self, devices: List[utils.DeviceInfo], limit_loaded_models:int=1) -> None:
        super().__init__()
        env_av_model_names = set(os.environ.get('WHISPER_AVALIABLE_MODELS', '').split(','))
        avaliable_model_names = set(_MODELS.keys()).intersection(env_av_model_names)
        avaliable_models = [whisper_models.WhisperModels[name].value for name in avaliable_model_names]
        models_devices = utils.match_device_models(devices, avaliable_models, exclude_nomatch=True)
        resolvable_models = set(models_devices.keys())

        self.avaliable_models = resolvable_models
        self.models_directory = Path(os.environ.get('WHISPER_MODELS_DIR', './data/models'))
        self.models_devices = models_devices
        self._loaded_models: OrderedDict[whisper_models.WhisperModelsNames, _LoadedModel] = OrderedDict()
        self.limit_loaded_models = limit_loaded_models


    def transcribe(self, file: Path, model_name: str, datetime_base: datetime = None):
        model = self._get_model(model_name=model_name)
        result = model.model_ml.transcribe(str(file.resolve()))

        if datetime_base is None:
            datetime_base = datetime.now()
        text = self._result_to_txt(result, datetime_base)

        return {
            'text': text,
            'datetime_base': datetime_base,
            'result': result
        }


    def _get_model(self, model_name: str):
        if model_name not in self.avaliable_models:
            raise Exception(f"Model '{model_name}' not avaliable! (Avaliabled models: {','.join(self.avaliable_models)})")

        cached_model = self._loaded_models.get(model_name)
        if cached_model is not None:
            return cached_model

        device = self.models_devices[model_name]
        logger.info(f"Using device '{device.name}' to load model '{model_name}'.")

        self._loaded_models = OrderedDict()
        model = load_model(model_name, torch.device(device.idx), self.models_directory)
        self._loaded_models[model_name] = _LoadedModel(model_ml=model, model_info=m_info(model_name))
        self._loaded_models = OrderedDict(sorted(self._loaded_models.items(), key=lambda m: m[1].model_info.mem_usage))

        logger.info(f"Loaded! Models in memory: {list(self._loaded_models.keys())}")
        return self._loaded_models[model_name]

        

    def _free_model(self, model_name: str):
        if model_name not in self.avaliable_models:
            raise Exception(f"Model '{model_name}' not avaliable! (Avaliabled models: {','.join(self.avaliable_models)})")

        cached_model = self._loaded_models.get(model_name)
        if cached_model is not None:
            self._loaded_models.pop(model_name)
            logger.info(f"Model '{model_name}' removed from memory.")
            return True

        return False


    def download_avaliable_models(self):
        for name in self.avaliable_models:
            logger.info("Trying to download avaliable models...")
            _download(_MODELS[name], self.models_directory, False)
            logger.info("All models has been downloaded.")


    def is_model_avaliable(self, model: str):
        return model in self.avaliable_models

    def _filter_dates(dd):
        date_text, date_time = dd
        result = True
        
        if date_text.count(' ') != 1:
            result = False

        dig_count = sum(i.isdigit() for i in date_text)
        if not (0 < dig_count < 3):
            result = False

        return result


    def _result_to_txt(self, res: dict, datetime_base: datetime=None):

        segments = tighten_timestamps(res,
            end_at_last_word=False,
            end_before_period=False,
            start_at_first_word=False)['segments']

        regex = r"\W\d{1,2}(-го)? \w{3,10}\W"

        def format_segment(seg):
            start = Whisper._chop_microseconds(timedelta(seconds=seg['start']))
            end = Whisper._chop_microseconds(timedelta(seconds=seg['end']))

            def replacer_date(match: 're.Match'):
                date_str: str = match.group(0)
                day, month = date_str[1:-1].split()
                month_lower = month.lower()
                
                (month_i, month) = next(filter(lambda m_s: month_lower.startswith(m_s[1]), 
                    enumerate(_ru_month_starts)), (None, None))
                if month is None: 
                    return date_str
                month_i += 1

                day_i = int(''.join(itertools.islice(filter(str.isdigit, day), 2)))
                if 1 > day_i > 31: 
                    return date_str

                n = datetime_base #datetime.now()
                is_future_date = (n.month > month_i) or (n.month == month_i and n.day > day_i)
                year_i = n.year+1 if is_future_date else n.year

                min_day_i, max_day_i = calendar.monthrange(year_i, month_i)
                if min_day_i > day_i > max_day_i:
                    return date_str

                
                d = datetime(year=year_i, month=month_i, day=day_i)
                return f"{date_str[0]}[{date_str[1:-1]}]({d.strftime('%d.%m.%Y')}){date_str[-1]}"

            text_w_dates = re.sub(regex, replacer_date, seg['text'], 0, re.UNICODE)
            

            return f"[{start}-{end}] {text_w_dates}"

        lines = [format_segment(seg) for seg in segments]
        return lines
    

    def _chop_microseconds(delta):
        return delta - timedelta(microseconds=delta.microseconds)



def m_info(model: whisper_models.WhisperModels):
    return whisper_models.WhisperModels[model].value

def mem(model: whisper_models.WhisperModels):
    return model.mem_usage