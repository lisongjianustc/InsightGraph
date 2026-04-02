# 使用官方 Python 运行时作为父镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖，特别是 OpenCV (pdf2zh的底层依赖) 需要的共享库
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        libxcb1 \
        libx11-xcb1 \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将当前目录内容复制到容器的 /app 内
COPY . /app

# 暴露端口
EXPOSE 8000

# 运行 FastAPI 应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
