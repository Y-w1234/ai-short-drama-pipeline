FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY main.py .
COPY .env.example .env

# 创建输出目录
RUN mkdir -p output

# 健康检查（每 30s 验证 demo 模式可运行）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from main import ShortDramaPipeline; ShortDramaPipeline().run('测试')" || exit 1

# Demo 模式运行（无需 API Key）
CMD ["python", "main.py", "--output", "output/short_drama_result.json"]
