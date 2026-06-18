# option-feeder

为 Trading Core 提供期权链数据的独立 Cron 服务：从 yfinance 拉取指定 ticker 的期权链，标准化后推送到 Core 的 ingest 接口。

## 架构

```
yfinance → normalize → POST /internal/ingest/option-chain (Trading Core)
```

- **无状态**：每次 Cron 触发跑完即退出，不保留本地数据
- **单 ticker 单 Service**：通过环境变量 `TICKER` 区分，多 ticker 需复制 Railway Service
- **批次对齐**：`batch_id` 按 UTC 5 分钟向下取整，便于多 Feeder 对齐观测
- **开市过滤**：非美股交易时段自动 `SKIP`，不推送

## 本地运行

```bash
cp .env.example .env
# 编辑 .env 填入 TICKER、INGEST_URL、INGEST_API_KEY

pip install -r requirements.txt
python -m app.main
```

## Railway 部署

1. 将本仓库连接到 Railway Project（GitHub 集成）
2. 使用根目录 `Dockerfile` 构建（`railway.json` 已指定 `DOCKERFILE` builder）
3. 在 Service Settings 确认 Cron Schedule 为 `*/5 * * * *`（UTC，每 5 分钟；与 `railway.json` 中 `cronSchedule` 一致）
4. 配置环境变量（每个 Service 独立）：

| 变量 | 必填 | 说明 |
|------|------|------|
| `TICKER` | 是 | 标的代码，如 `NVDA` |
| `INGEST_URL` | 是 | Core ingest 完整 URL |
| `INGEST_API_KEY` | 是 | Bearer token |
| `EXPIRY_DTE_MAX` | 否 | 只取 DTE ≤ 此值的到期日，缩短耗时；留空=全取 |
| `JITTER_MAX` | 否 | 错峰上限（秒），默认 `20` |
| `MAX_RETRY` | 否 | 取链/推送重试次数，默认 `2` |

5. 多 ticker：复制 Service，仅修改 `TICKER` 即可

### 注意事项

- Cron 服务必须 `restartPolicyType: NEVER`（已写入 `railway.json`）
- 若单次任务超过 5 分钟，下一轮 Cron 会被跳过；大 ticker 建议设置 `EXPIRY_DTE_MAX=60`
- 下游 Core 须已部署且 ingest 端点可从 Railway 公网访问
- 日志为 JSON 结构化输出到 stdout，可在 Railway Logs 查看 `START` / `SUCCESS` / `FAILED` / `SKIP` 等事件

## 推送协议

见 `models/payload.py`。`contract_key` 由 Trading Core 侧统一生成，feeder 不携带。
