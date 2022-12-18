import environ, os, ipaddress
from pathlib import Path


@environ.config
class AppConfig:    
    temp_directory: Path = environ.var(converter=Path, default=Path('./astra_data/temp'))

    @environ.config
    class WhisperConfig:
        models: list = environ.var(converter=lambda s: s.split(), default='tiny small base')
        default_model: str = environ.var(default='small')
        model_directory: Path = environ.var(converter=Path, default='./astra_data/models')
    whisper: WhisperConfig = environ.group(WhisperConfig)
    

    @environ.config
    class TaskQueueConfig:
        broker_uri: str = environ.var()
        remove_source_files: bool = environ.bool_var(default=True)
    taskqueue: TaskQueueConfig = environ.group(TaskQueueConfig)  

    @environ.config
    class DBConfig:
        database_uri: str = environ.var()
    db: DBConfig = environ.group(DBConfig)    
    
    
    @environ.config
    class ApiConfig:
        host: ipaddress.IPv4Address = environ.var(default='192.1.0.0', converter=ipaddress.IPv4Address)
        port: int = environ.var(default=8000, converter=int)
    api: ApiConfig = environ.group(ApiConfig)
    
cfg: AppConfig = AppConfig.from_environ(os.environ)

cfg.temp_directory.mkdir(parents=True, exist_ok=True)
cfg.whisper.model_directory.mkdir(parents=True, exist_ok=True)

print(cfg)

__all__ = [cfg]