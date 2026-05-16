from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Never

from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent.parent.resolve() / ".env"
TOML_PATH = Path(__file__).parent.resolve() / "config.toml"

load_dotenv(dotenv_path=ENV_PATH)

with open(TOML_PATH, "rb") as toml:
    toml_data = tomllib.load(toml)


@dataclass
class APIURLs:
    prefix: str
    docs_endpoint: str
    redoc_endpoint: str
    openapi_endpoint: str

    @classmethod
    def from_toml(cls) -> APIURLs:
        return cls(
            toml_data["api"]["prefix"],
            toml_data["api"]["prefix"] + toml_data["api"]["docs_endpoint"],
            toml_data["api"]["prefix"] + toml_data["api"]["redoc_endpoint"],
            toml_data["api"]["prefix"] + toml_data["api"]["openapi_endpoint"]
        )


@dataclass
class CorsConfig:
    use_cors: bool
    allow_credentials: bool
    allowed_origins: list[str] | list[Never] = field(default_factory=list)
    allowed_methods: list[str] | list[Never] = field(default_factory=list)
    allowed_headers: list[str] | list[Never] = field(default_factory=list)

    @classmethod
    def from_toml(cls) -> CorsConfig:
        return cls(
            toml_data["api"]["cors"]["use_cors"],
            toml_data["api"]["cors"]["allow_credentials"],
            toml_data["api"]["cors"]["allowed_origins"],
            toml_data["api"]["cors"]["allowed_methods"],
            toml_data["api"]["cors"]["allowed_headers"]
        )


@dataclass
class APIConfig:
    key: str
    port: int

    urls: APIURLs
    cors: CorsConfig

    activate_rate_limits: bool
    default_rate_limits: str

    telemetry_limit: int

    @classmethod
    def from_toml(cls) -> APIConfig:
        return cls(
            os.getenv("API_KEY"),
            int(os.getenv("API_PORT")),
            APIURLs.from_toml(),
            CorsConfig.from_toml(),
            toml_data["api"]["rate_limiting"]["activate_rate_limits"],
            os.getenv("DEFAULT_RATE_LIMIT"),
            toml_data["api"]["telemetry"]["telemetry_limit"]
        )


@dataclass
class MLConfig:
    prediction_horizons: list[int]

    @classmethod
    def from_toml(cls) -> MLConfig:
        return cls(
            toml_data["ml"]["prediction_horizons"]
        )


@dataclass
class DBConfig:
    path: Path

    @classmethod
    def from_toml(cls) -> DBConfig:
        return cls(
            Path(__file__).parent.parent.resolve() / "database" / "storage.db"
        )


@dataclass
class FrontendConfig:
    password: str
    port: int

    @classmethod
    def from_toml(cls) -> FrontendConfig:
        return cls(
            os.getenv("FRONTEND_PASSWORD"),
            int(os.getenv("STREAMLIT_PORT"))
        )


@dataclass
class OtherConfig:
    ignore_warnings: bool

    @classmethod
    def from_toml(cls) -> OtherConfig:
        return cls(
            toml_data["other"]["ignore_warnings"]
        )


@dataclass
class Config:
    api: APIConfig
    ml: MLConfig
    db: DBConfig
    frontend: FrontendConfig
    other: OtherConfig

    version: str
    base_url: str

    @classmethod
    def from_toml(cls) -> Config:
        return cls(
            APIConfig.from_toml(),
            MLConfig.from_toml(),
            DBConfig.from_toml(),
            FrontendConfig.from_toml(),
            OtherConfig.from_toml(),
            "0.1.0",
            os.getenv("BASE_URL")
        )


settings = Config.from_toml()
