FROM python:3.9

# 安装系统依赖
RUN apt update -y && apt install -y ffmpeg

# 设置工作目录
WORKDIR /app

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --no-check-hashes -r requirements.txt

# 复制应用代码
COPY . .

# 预加载Whisper模型
RUN whisper audio.mp4 --model turbo

# 暴露端口
EXPOSE 8100

# 启动应用
CMD ["python", "main.py"]
