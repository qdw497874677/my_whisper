FROM python:3.9

# 使用国内镜像源加速构建
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 分步安装系统依赖
RUN apt update -y
RUN apt install ffmpeg -y

# 设置工作目录
WORKDIR /app

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制应用代码
COPY . .

# 预加载Whisper模型
RUN whisper audio.mp4 --model turbo

# 暴露端口
EXPOSE 8100

# 启动应用
CMD ["python", "main.py"]
