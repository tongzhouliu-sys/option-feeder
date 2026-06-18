"""环境变量配置(强类型校验)。每个 Service 仅靠 TICKER 区分。"""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Only load a .env file when one is actually present on disk (local development).
# In production (Railway), environment variables are injected by the platform and
# no .env file exists in the container, so we skip it to avoid masking real env vars.
_env_file = ".env" if Path(".env").exists() else None


class Settings(BaseSettings):
    # —— 必填(每个 Service 独立注入)——
    TICKER: str
    INGEST_URL: str
    INGEST_API_KEY: str

    # —— 数据源 —— (Phase 2 切 Polygon/IBKR 时改这一个值即可)
    DATA_SOURCE: str = "yfinance"
    MARKET: str = "US"

    # —— 网络/重试 ——
    REQUEST_TIMEOUT: int = 15          # 单次外部请求超时(s)
    INGEST_TIMEOUT: int = 15           # 推送 Core 超时(s)
    MAX_RETRY: int = 2                 # 取链/推送的重试次数

    # —— 防风控抖动 —— 错峰发起,避免 117 个 Service 同一秒打 yfinance
    JITTER_MIN: int = 0
    JITTER_MAX: int = 20

    # —— 可选性能杠杆 —— 只取 DTE <= 此值的到期(None=全取,保持原行为)
    EXPIRY_DTE_MAX: Optional[int] = None

    model_config = SettingsConfigDict(env_file=_env_file, env_file_encoding="utf-8")


settings = Settings()
