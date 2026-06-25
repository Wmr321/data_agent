from dataclasses import dataclass
from pathlib import Path
from omegaconf import OmegaConf

@dataclass
class LoggingFile:
    enable: bool
    level: str
    path: str
    rotation: str
    retention: str


@dataclass
class LoggingConsole:
    enable: bool
    level: str


@dataclass
class LoggingConfig:
    file: LoggingFile
    console: LoggingConsole


@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int


@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str


@dataclass
class EsConfig:
    host: str
    port: int
    index_name: str


@dataclass
class LlmConfig:
    text_model:str
    text_model_temperature: float
    code_model: str
    code_model_temperature: float
    api_key: str
    base_url: str

@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: EsConfig
    llm: LlmConfig

app_config_path = Path(__file__).parents[2] / 'conf' / 'app_config.yaml'
app_config_content = OmegaConf.load(app_config_path)

app_config_schema = OmegaConf.structured(AppConfig)

app_config: AppConfig = OmegaConf.to_object(OmegaConf.merge(app_config_schema, app_config_content))


