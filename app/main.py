"""程序入口。run() 失败 -> 退出码 1,便于 Railway / 监控感知。"""
import sys

from app.config import settings
from clients.market_client import MarketClient
from clients.ingest_client import IngestClient
from services.feeder_service import FeederService
from utils.logger import log


def main() -> None:
    feeder = FeederService(
        ticker=settings.TICKER,
        market_client=MarketClient(
            max_retry=settings.MAX_RETRY,
            expiry_dte_max=settings.EXPIRY_DTE_MAX,
        ),
        ingest_client=IngestClient(
            settings.INGEST_URL, settings.INGEST_API_KEY, timeout=settings.INGEST_TIMEOUT
        ),
        settings=settings,
    )
    try:
        ok = feeder.run()
    except Exception as e:                       # 兜底:任何未捕获异常都不留栈,记 FAILED
        log({"event": "FAILED", "ticker": settings.TICKER, "stage": "fatal", "reason": str(e)})
        sys.exit(1)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
