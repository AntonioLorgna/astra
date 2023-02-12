
from dataclasses import dataclass
from typing import Dict, List
import platform, os, hashlib, base64, threading, asyncio


from astra.whisper_static import WhisperModelInfo, WhisperModelsNames, WhisperModels

@dataclass()
class DeviceInfo:
    name: str
    memory: int
    cores: int
    architecture: str
    idx: int|str

    def __repr__(self) -> str:
        return \
            f"""Device name: {self.name}
            Avaliable memory: {self.memory / (1<<20)}MB
            Cores: {self.cores}
            Architecture: {self.architecture}"""

def get_devices(exclude_cpu=False):
    import torch as th
    devices = []

    if not exclude_cpu:
        cpu = DeviceInfo(
            name=platform.processor(),
            architecture='cpu',
            cores=os.cpu_count(),
            memory=os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES'),
            idx='cpu'
        )
        devices.append(cpu)

    if th.cuda.is_available():
        available_gpus = [th.cuda.device(i) for i in range(th.cuda.device_count())]
        
        def build_device_info(thdevice: th.cuda.device)-> DeviceInfo:
            properties = th.cuda.get_device_properties(thdevice.idx)
            device = DeviceInfo(
                name=properties.name,
                cores=properties.multi_processor_count,
                architecture='cuda',
                memory=properties.total_memory,
                idx=thdevice.idx
            )
            return device

        devices.extend([build_device_info(thdevice) for thdevice in available_gpus])


    return devices

def match_device_models(devices: List[DeviceInfo], models: List[WhisperModelInfo], exclude_nomatch=True)->Dict[WhisperModelsNames, DeviceInfo]:
    devices = devices.copy()
    devices.sort(key=lambda d: d.memory)
    def match_(model: WhisperModelInfo, devices: List[DeviceInfo]):
        for device in devices:
            if model.mem_usage < device.memory:
                return device
        return None
    
    return {model.name:device 
        for model in models if 
        (device := match_(model, devices)) is not None or not exclude_nomatch}

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


def hash(data: bytes)->str:
    """Генерирует хэш sha256 и кодирует в base64 и в строку utf-8.

    Args:
        data (bytes): Байты для кодировки.

    Returns:
        str: Строка содержащая base64 символы длиной 44.
    """
    
    hash_d = hashlib.sha256(data).digest()
    b64 = base64.urlsafe_b64encode(hash_d)
    return b64.decode('utf-8')



def fire_and_forget(coro):
    _loop = asyncio.new_event_loop()
    threading.Thread(target=_loop.run_forever, daemon=True).start()
    _loop.call_soon_threadsafe(asyncio.create_task, coro)


