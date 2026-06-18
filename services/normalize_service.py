"""数据清洗(向量化,避免 iterrows)。NaN -> None,转 Contract 列表。"""
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from models.payload import OptionPayload, Contract


def _records(df) -> list:
    """DataFrame -> dict 列表;NaN 统一转 None,防 Pydantic 校验报错。"""
    if df is None or getattr(df, "empty", True):
        return []
    return df.replace({np.nan: None}).to_dict("records")


def _build(rows: list, expiry: str, right: str) -> list:
    out = []
    for row in rows:
        strike = row.get("strike")
        if strike is None:                       # 缺 strike 的行无意义,跳过
            continue
        out.append(Contract(
            expiry=expiry,
            strike=float(strike),
            right=right,
            bid=row.get("bid"),
            ask=row.get("ask"),
            last=row.get("lastPrice"),
            volume=row.get("volume"),
            open_interest=row.get("openInterest"),
            iv=row.get("impliedVolatility"),
        ))
    return out


def normalize(ticker: str, chains: list, batch_id: str) -> dict:
    contracts = []
    for item in chains:
        expiry = item["expiry"]
        contracts += _build(_records(item.get("calls")), expiry, "C")
        contracts += _build(_records(item.get("puts")), expiry, "P")

    return OptionPayload(
        source="yfinance",
        batch_id=batch_id,
        ticker=ticker,
        quote_time=datetime.now(timezone.utc).isoformat(),
        contracts=contracts,
    ).model_dump()
