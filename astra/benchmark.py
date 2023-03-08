from os import environ
from pathlib import Path
import stable_whisper
from whisper import Whisper
from time import time
import ffmpeg
import numpy as np
from tqdm import tqdm
import logging
from pickle import dump as pkl_dump
from json import dump as json_dump


def logging_setup(
    logger=None, level=logging.INFO, formatter="%(levelname)s: %(message)s"
):
    import logging
    from sys import stdout

    if logger is None:
        logger = logging.getLogger(__name__)

    logger.setLevel(level)
    logFormatter = logging.Formatter(formatter)

    consoleHandler = logging.StreamHandler(stdout)
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)


logger = logging.getLogger(__name__)
logging_setup(logger)

MEDIA_SRC_DIR = Path("data/media")
if environ.get("MEDIA_SRC_DIR") is not None:
    MEDIA_SRC_DIR = Path(environ.get("MEDIA_SRC_DIR"))
else:
    logger.warning(f"Not setted env var MEDIA_SRC_DIR, using default '{MEDIA_SRC_DIR}'")
MEDIA_SRC_DIR.mkdir(exist_ok=True)


RESULT_DIST_DIR = Path("data/results")
if environ.get("RESULT_DIST_DIR") is not None:
    RESULT_DIST_DIR = Path(environ.get("RESULT_DIST_DIR"))
else:
    logger.warning(
        f"Not setted env var RESULT_DIST_DIR, using default '{RESULT_DIST_DIR}'"
    )
RESULT_DIST_DIR.mkdir(exist_ok=True)


MODELS_DIR = Path("data/models")
if environ.get("MODELS_DIR") is not None:
    MODELS_DIR = Path(environ.get("MODELS_DIR"))
else:
    logger.warning(f"Not setted env var MODELS_DIR, using default '{MODELS_DIR}'")
MODELS_DIR.mkdir(exist_ok=True)


MODELS_TO_BENCH = ["tiny", "base", "small", "medium", "large"]
if environ.get("MODELS_TO_BENCH") is not None:
    MODELS_TO_BENCH = environ.get("MODELS_TO_BENCH").split(",")
else:
    logger.warning(
        f"Not setted env var MODELS_TO_BENCH, using default '{MODELS_TO_BENCH}'"
    )


DEVICE = "cuda"
SAMPLE_RATE = 16000


def audio_bytes_to_arr_f32(b: bytes) -> np.ndarray:
    return np.frombuffer(b, np.float32)


def load_file(file: str | Path, sr=SAMPLE_RATE):
    process1 = (
        ffmpeg.input(str(file))
        .output("pipe:", format="f32le", acodec="pcm_f32le", ac=1, ar=sr)
        .run_async(pipe_stdout=True)
    )
    audio = audio_bytes_to_arr_f32(process1.stdout.read())

    process1.stdout.close()
    process1.wait()
    return audio


def transcribe(
    model: Whisper, model_name: str, src_audio_path: Path, dist_result_path: Path
):
    src_audio = load_file(src_audio_path).copy()
    _t_start = time()
    res = model.transcribe(src_audio, verbose=None)
    _t_end = time()
    res["execution_time_sec"] = _t_end - _t_start
    res["model_name"] = model_name
    res["device"] = str(DEVICE)

    with dist_result_path.with_suffix(".pkl").open("wb") as dist_f:
        pkl_dump(res, dist_f)

    stable_whisper.save_as_json(res, str(dist_result_path.with_suffix(".json")))
    return res["execution_time_sec"]


def prepare_files():
    src_files = [f for f in MEDIA_SRC_DIR.iterdir() if f.is_file()]
    return src_files


def dist_filename_for_model(src_file: Path, model_name: str):
    dist_file = RESULT_DIST_DIR / src_file.with_suffix("").name
    return dist_file.with_name(f"{model_name[0]}{model_name[-1]}_{dist_file.name}")


def main():
    src_files = prepare_files()
    for model_name in tqdm(MODELS_TO_BENCH):
        model = stable_whisper.load_model(model_name, DEVICE, str(MODELS_DIR))
        for src_file in tqdm(src_files):
            dist_file = dist_filename_for_model(src_file, model_name)
            exec_time = transcribe(model, model_name, src_file, dist_file)
            logger.info(f"#### File executed for {exec_time} sec. ####")

    logger.info(f"############################################")
    logger.info(f"################### DONE ###################")
    logger.info(f"############################################")


if __name__ == "__main__":
    main()
