FROM python:3.11-slim

WORKDIR /app

# numpy/pandas/exchange_calendars 均有 wheel;通常无需 gcc。
# 若某依赖在你的架构上需编译,取消下一行注释。
# RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "app.main"]
