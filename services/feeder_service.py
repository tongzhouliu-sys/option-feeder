"""核心编排:Jitter -> 批次对齐 -> 取链 -> 标准化 -> 推送。无状态,跑完即退。

取链由 MarketClient 内部重试;推送由 utils.retry 按 HTTP 状态码重试。
任一阶段异常只记录,不抛栈崩溃(绝不断流);推送彻底失败时 run() 返回 False,
由 main 决定退出码,便于 Railway / 监控感知。
"""
import random
import time
from datetime import datetime, timezone

from utils.logger import log
from utils.retry import retry
from services.normalize_service import normalize
from services.market_hours import is_market_open


class FeederService:
    def __init__(self, ticker, market_client, ingest_client, settings):
        self.ticker = ticker
        self.market_client = market_client
        self.ingest_client = ingest_client
        self.settings = settings

    def _aligned_batch_id(self) -> str:
        """UTC 向下取整到最近 5 分钟,确保 117 个 Feeder 批次对齐。"""
        now = datetime.now(timezone.utc)
        bucket = now.replace(minute=(now.minute // 5) * 5, second=0, microsecond=0)
        return bucket.strftime("%Y%m%d_%H%M")

    def run(self) -> bool:
        if not is_market_open():
            log({"event": "SKIP", "ticker": self.ticker, "reason": "MARKET_CLOSED"})
            return True

        started = time.time()
        batch_id = self._aligned_batch_id()
        idem = f"{self.ticker}_{batch_id}"
        log({"event": "START", "ticker": self.ticker, "batch_id": batch_id})

        # 错峰
        time.sleep(random.uniform(self.settings.JITTER_MIN, self.settings.JITTER_MAX))

        # 取链(内部已重试);彻底失败 -> 记 FAILED,不推空(Core 侧靠 upsert 保留上一份)
        try:
            chains = self.market_client.get_option_chain(self.ticker)
        except Exception as e:
            log({"event": "FAILED", "ticker": self.ticker, "batch_id": batch_id,
                 "stage": "fetch", "reason": str(e)})
            return False

        if not chains:
            log({"event": "NO_DATA", "ticker": self.ticker, "batch_id": batch_id})
            return True

        payload = normalize(self.ticker, chains, batch_id)
        if not payload["contracts"]:
            log({"event": "NO_DATA", "ticker": self.ticker, "batch_id": batch_id,
                 "reason": "EMPTY_AFTER_NORMALIZE"})
            return True

        # 推送(HTTP 重试)
        try:
            retry(lambda: self.ingest_client.push(payload, idem), self.settings.MAX_RETRY)
        except Exception as e:
            log({"event": "FAILED", "ticker": self.ticker, "batch_id": batch_id,
                 "stage": "ingest", "reason": str(e)})
            return False

        duration = int((time.time() - started) * 1000)
        log({"event": "SUCCESS", "ticker": self.ticker, "batch_id": batch_id,
             "contracts_count": len(payload["contracts"]), "duration_ms": duration,
             "status": "HEALTHY" if duration < 15000 else "DEGRADED"})
        return True
