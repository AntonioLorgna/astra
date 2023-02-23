from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List
import platform, os, hashlib, base64, threading, asyncio
from logging import getLogger

from pydantic import UUID4
from astra.core import schema
import logging
import json

logger = getLogger(__name__)

@dataclass()
class DeviceInfo:
    name: str
    memory: int
    cores: int
    architecture: str
    idx: int | str

    def __repr__(self) -> str:
        return f"""Device name: {self.name}
            Avaliable memory: {self.memory / (1<<20)}MB
            Cores: {self.cores}
            Architecture: {self.architecture}"""


def get_devices(exclude_cpu=False):
    import torch as th

    devices = []

    if not exclude_cpu:
        cpu = DeviceInfo(
            name=platform.processor(),
            architecture="cpu",
            cores=os.cpu_count(),
            memory=os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"),
            idx="cpu",
        )
        devices.append(cpu)

    if th.cuda.is_available():
        available_gpus = [th.cuda.device(i) for i in range(th.cuda.device_count())]

        def build_device_info(thdevice: th.cuda.device) -> DeviceInfo:
            properties = th.cuda.get_device_properties(thdevice.idx)
            device = DeviceInfo(
                name=properties.name,
                cores=properties.multi_processor_count,
                architecture="cuda",
                memory=properties.total_memory,
                idx=thdevice.idx,
            )
            return device

        devices.extend([build_device_info(thdevice) for thdevice in available_gpus])

    return devices


def match_device_models(
    devices: List[DeviceInfo], models: List[str], exclude_nomatch=True
) -> Dict[str, DeviceInfo]:
    from astra.core.whisper_models import WhisperModels

    devices = devices.copy()
    devices.sort(key=lambda d: d.memory)

    def match_(modelname: str, devices: List[DeviceInfo]):
        for device in devices:
            if WhisperModels.mem_usage(modelname) < device.memory:
                return device
        return None

    return {
        modelname: device
        for modelname in models
        if (device := match_(modelname, devices)) is not None or not exclude_nomatch
    }


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


def logging_setup(logger=None, level=logging.INFO, formatter="%(levelname)s: %(message)s"):
    import logging
    from sys import stdout

    if logger is None:
        logger = logging.getLogger(__name__)

    logger.setLevel(level)
    logFormatter = logging.Formatter(formatter)

    consoleHandler = logging.StreamHandler(stdout)
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)



def fire_and_forget(coro):
    from concurrent.futures import ThreadPoolExecutor
    loop = asyncio.new_event_loop()
    executor = ThreadPoolExecutor(max_workers=2)
    loop.run_in_executor(executor)
    threading.Thread(target=loop.run_forever, daemon=True).start()
    loop.call_soon_threadsafe(asyncio.create_task, coro)


def show_execute_path():
    from pathlib import Path
    p = Path('./')
    return str(p.resolve(True))


def devport_init(wait_for_connection=False):
    if os.environ.get("DEV_PORT") is not None:
        port = int(os.environ.get("DEV_PORT"))
        import debugpy
        debugpy.listen(("0.0.0.0", port))
        if wait_for_connection:
            debugpy.wait_for_client()

def hash(data: bytes):
    return hashlib.sha256(data).digest()

def hash_stringify(hash_digest: bytes):
    b64 = base64.urlsafe_b64encode(hash_digest)
    return b64.replace(b'=', b'').decode("utf-8")

class HashIO:
    def __init__(self, algo = hashlib.sha256) -> None:
        self._hash = algo()

    def update(self, buffer: bytes):
        self._hash.update(buffer)
        return self
    
    def digest(self):
        return self._hash.digest()
    def hexdigest(self):
        return self._hash.hexdigest()
    
    def __str__(self) -> str:
        return hash_stringify(self._hash.digest())

    def __repr__(self) -> str:
        return str(self)

def result_stringify(result: schema.TranscribeResult, spliter: str="\n"):
    return spliter.join([seg.text for seg in result.segments])


def uuid_short(id: str|UUID4, lenght: int = 8):
    return str(id).split('-')[0][:lenght]

def uuid_tag(id: str|UUID4):
    return f"#T{uuid_short(id)}"


def get_ngrok_hostname():
    import requests

    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=3)
        if not response.ok: return None
   
        return response.json()['tunnels'][0]['public_url']
    except KeyError or ConnectionError:
        return None