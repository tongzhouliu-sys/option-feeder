"""推送协议(Pydantic v2)。Core 端据此解析并入库。

注意:本模型不携带 contract_key —— contract_key 由 Trading Core 经
store.make_contract_key(ticker, strike, expiry, right) 统一拼接(IBKRv5 CODE_STYLE §2)。
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict


class Contract(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    expiry: str                          # YYYY-MM-DD
    strike: float
    right: Literal["C", "P"]

    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None

    volume: Optional[int] = None
    open_interest: Optional[int] = None
    iv: Optional[float] = None            # yfinance: impliedVolatility,在 normalize 显式映射


class OptionPayload(BaseModel):
    source: str                          # 数据源标记(yfinance / polygon / ibkr)
    batch_id: str                        # 5 分钟对齐桶,用于 Core 侧批次/新鲜度观测
    ticker: str
    quote_time: str                      # 实际取数时刻(ISO8601 UTC)
    contracts: List[Contract]
