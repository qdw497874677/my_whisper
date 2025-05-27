FROM whisper:latest

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

RUN whisper audio.mp4 --model turbo

EXPOSE 8100
CMD ["python", "main.py"]