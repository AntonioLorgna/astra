
from dataclasses import dataclass
from typing import Dict, List

from whisper_static import WhisperModelInfo, WhisperModelsNames, WhisperModels

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
        import platform, os
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