"""交易时间与节假日控制(纽交所 XNYS,自动处理半天交易日)。"""
import pandas as pd
import exchange_calendars as xcals

_calendar = xcals.get_calendar("XNYS")


def is_market_open() -> bool:
    """当前是否为美股正常交易时段。日历异常时保守返回 False(跳过本轮)。"""
    try:
        now = pd.Timestamp.now(tz="UTC")
        if not _calendar.is_session(now.normalize().tz_localize(None)):
            return False
        return bool(_calendar.is_open_on_minute(now))
    except Exception:
        return False
