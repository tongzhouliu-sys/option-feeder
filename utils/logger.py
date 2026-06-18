"""JSON 结构化日志(stdout,适配容器日志收集)。"""
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)


def log(data: dict) -> None:
    logging.info(json.dumps(data, ensure_ascii=False))
