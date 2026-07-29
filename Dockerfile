FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY main.py .
COPY web_ui.py .
COPY .env.example .env

# 创建输出目录
RUN mkdir -p output

# 暴露 Streamlit 端口
EXPOSE 7860

# 健康检查（每 30s 验证 demo 模式可运行）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from main import ShortDramaPipeline; ShortDramaPipeline().run('测试')" || exit 1

# Web UI 模式（默认）
CMD ["streamlit", "run", "web_ui.py", "--server.port=7860", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
