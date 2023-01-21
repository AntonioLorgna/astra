from datetime import datetime
from pathlib import Path
from sys import stdout
from stable_whisper import load_model
from stable_whisper.stabilization import tighten_timestamps
import torch
from whisper import _download, _MODELS
from datetime import timedelta, datetime
from pathlib import Path
import re, itertools, os
import calendar
import logging
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

device_name = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device '{device_name}' for ML.")

class Whisper:
    AVALIABLE_MODELS = os.environ.get('WHISPER_AVALIABLE_MODELS').split(',')
    MODELS_DIR = Path(os.environ.get('WHISPER_MODELS_DIR'))
    loaded_models = dict()

    def transcribe(file: Path, model_name: str, datetime_base: datetime = None):
        model = Whisper._get_model(model_name=model_name)
        result = model.transcribe(str(file.resolve()))

        if datetime_base is None:
            datetime_base = datetime.now()
        text = Whisper._result_to_txt(result, datetime_base)

        Whisper._free_model(model)

        return {
            'text': text,
            'datetime_base': datetime_base,
            'result': result
        }


    def _get_model(model_name: str):
        if model_name not in Whisper.AVALIABLE_MODELS:
            raise Exception(f"Model '{model_name}' not avaliable! (Avaliabled models: {','.join(Whisper.AVALIABLE_MODELS)})")

        cached_model = Whisper.loaded_models.get(model_name)
        if cached_model is None:
            device_name = "cuda" if torch.cuda.is_available() else "cpu"
            device = torch.device(device_name)
            logger.info(f"Using device '{device_name}' to load model '{model_name}'.")
            model = load_model(model_name, device, Whisper.MODELS_DIR)
            Whisper.loaded_models[model_name] = model

            logger.info(f"Loaded! Models in memory: {list(Whisper.loaded_models.keys())}")
            return model
        
        return cached_model


    def _free_model(model_name: str):
        if model_name not in Whisper.AVALIABLE_MODELS:
            raise Exception(f"Model '{model_name}' not avaliable! (Avaliabled models: {','.join(Whisper.AVALIABLE_MODELS)})")

        cached_model = Whisper.loaded_models.get(model_name)
        if cached_model is not None:
            Whisper.loaded_models.pop(model_name)
            logger.info(f"Model '{model_name}' removed from memory.")
            return True

        return False


    def download_avaliable_models():
        for av_model_name in Whisper.AVALIABLE_MODELS:
            logger.info("Trying to download avaliable models...")
            _download(_MODELS[av_model_name], Whisper.MODELS_DIR, False)
            logger.info("All models has been downloaded.")


    def validate_avaliable_models():
        for av_model_name in Whisper.AVALIABLE_MODELS:
            if av_model_name not in list(_MODELS.keys()):
                raise Exception(f"Bad avaliable model '{av_model_name}'! Real avaliable whisper models: {','.join(list(_MODELS.keys()))}")


    def _filter_dates(dd):
        date_text, date_time = dd
        result = True
        
        if date_text.count(' ') != 1:
            result = False

        dig_count = sum(i.isdigit() for i in date_text)
        if not (0 < dig_count < 3):
            result = False

        return result


    def _result_to_txt(res: dict, datetime_base: datetime=None):

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


Whisper.validate_avaliable_models()