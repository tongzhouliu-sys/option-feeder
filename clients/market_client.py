"""数据源隔离层(yfinance)。内部带退避重试 + 单到期局部容错。

设计:
- 取到期列表(client.options)最易触发限流 -> 内部重试(yfinance 异常类型不可靠,故广捕但有界)。
- 单个 expiry 取链失败 -> 记录并继续,不让一个坏到期拖垮整条链。
- 全部失败(连到期都拿不到)-> 抛出,由上层记 FAILED(数据保持上一份,绝不断流)。
"""
import time
from datetime import date, datetime
from typing import Optional

import yfinance as yf

from utils.logger import log


def _with_retry(fn, attempts: int, base_delay: float = 2.0):
    for i in range(attempts + 1):
        try:
            return fn()
        except Exception:
            if i >= attempts:
                raise
            time.sleep(base_delay if i == 0 else base_delay * 2.5)


def _within_dte(expiry: str, dte_max: Optional[int]) -> bool:
    if dte_max is None:
        return True
    try:
        d = datetime.strptime(expiry, "%Y-%m-%d").date()
        return (d - date.today()).days <= dte_max
    except Exception:
        return True


class MarketClient:
    def __init__(self, max_retry: int = 2, expiry_dte_max: Optional[int] = None):
        self.max_retry = max_retry
        self.expiry_dte_max = expiry_dte_max

    def get_option_chain(self, ticker: str) -> list:
        client = yf.Ticker(ticker)

        # 到期列表:带重试;彻底失败则抛出(上层记 FAILED)
        expiries = _with_retry(lambda: list(client.options), self.max_retry)
        if not expiries:
            raise RuntimeError(f"no expiries for {ticker}")

        result = []
        for expiry in expiries:
            if not _within_dte(expiry, self.expiry_dte_max):
                continue
            try:
                chain = client.option_chain(expiry)
                result.append({"expiry": expiry, "calls": chain.calls, "puts": chain.puts})
            except Exception as e:
                log({"event": "EXPIRY_FETCH_FAILED", "ticker": ticker,
                     "expiry": expiry, "reason": str(e)})
                continue
        return result
