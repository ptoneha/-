FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 加速 APT：强制 IPv4 + 使用国内镜像
RUN echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4 \
 && sed -i 's@deb.debian.org@mirrors.tuna.tsinghua.edu.cn@g; s@security.debian.org@mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list \
 && apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq5 \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
# 加速 PIP（如需更换源，可在构建时通过 --build-arg 覆盖）
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
RUN pip install --no-cache-dir -r /app/requirements.txt -i ${PIP_INDEX_URL}

COPY . /app

EXPOSE 8787

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8787"]


