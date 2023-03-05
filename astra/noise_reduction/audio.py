
from pathlib import Path

import ffmpeg
import numpy as np
SAMPLE_RATE = 16000

def load_file(file: str|Path, sr=SAMPLE_RATE):
    process1 = (
        ffmpeg
        .input(file)
        .output('pipe:', format="f32le", acodec="pcm_f32le", ac=1, ar=sr)
        .run_async(pipe_stdout=True)
    )
    audio = audio_bytes_to_arr_f32(process1.stdout.read())

    def wait():
        process1.stdout.close()
        process1.wait()
    return (audio, wait)

def save_file(file: str|Path, audio: np.ndarray, sr=SAMPLE_RATE):
    process2 = (
        ffmpeg
        .input('pipe:', format="f64le", acodec="pcm_f64le", ac=1, ar=sr)
        .output(str(file))
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )
    process2.stdin.write(audio_arr_to_bytes_f64(audio))

    def wait():
        process2.stdin.close()
        process2.wait()
    return (True, wait)

def audio_bytes_to_arr(b: bytes):
    return np.frombuffer(b, np.int16).flatten().astype(np.float32) / 32768.0
def audio_bytes_to_arr_f32(b: bytes)-> np.ndarray:
    return np.frombuffer(b, np.float32)


def audio_arr_to_bytes(a: np.ndarray):
    # max_value_int16 = (1 << 15) - 1
    return (a * (1 << 15) - 1).astype(np.int16)
def audio_arr_to_bytes_f64(a: np.ndarray):
    return a