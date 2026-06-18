"""推送(HTTP)重试:只重试网络波动与限流,业务 4xx 快速失败。

用于 ingest_client.push —— Core ingest 端点行为可控,按 HTTP 状态码判定重试。
yfinance 取链的重试在 market_client 内部单独处理(其异常类型不可靠)。
"""
import time
import requests

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def retry(fn, retry_count: int = 2):
    attempt = 0
    while True:
        try:
            return fn()
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status not in RETRYABLE_STATUS_CODES or attempt >= retry_count:
                raise
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt >= retry_count:
                raise
        # 仅在"可重试且未达上限"时退避后继续
        time.sleep(2 if attempt == 0 else 5)
        attempt += 1
