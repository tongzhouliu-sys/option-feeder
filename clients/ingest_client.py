"""推送客户端:复用 TCP 连接 + 幂等 Key。raise_for_status 让上层 retry 处理 5xx。"""
import requests

from utils.logger import log


class IngestClient:
    def __init__(self, url: str, api_key: str, timeout: int = 15):
        self.url = url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def push(self, payload: dict, idempotency_key: str) -> int:
        resp = self.session.post(
            self.url,
            json=payload,
            headers={"Idempotency-Key": idempotency_key},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        log({"event": "INGEST_OK", "ticker": payload.get("ticker"),
             "status": resp.status_code, "idempotency_key": idempotency_key})
        return resp.status_code
