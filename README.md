# Whisper API Service

A REST API service for speech-to-text transcription powered by OpenAI's Whisper model. This service provides an easy-to-use interface for audio transcription with support for multiple languages.

## Quick Start with Docker

```bash
docker run -p 8100:8100 hipc/whisper-api
```

Access the API at: http://localhost:8100

[中文文档](README_CN.md)

## Features

- Audio file upload for transcription
- Audio URL transcription support
- Asynchronous task processing
- Task status tracking
- Language specification support
- Task deduplication based on file hash
- SQLite-based task persistence

## Requirements

- Python 3.8+
- FFmpeg (for audio processing)
- CUDA support (optional, for GPU acceleration)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd whisper-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the service:
```bash
python main.py
```

The service will start at http://localhost:8100

## API Documentation

### 1. Upload Audio File
- **Endpoint**: `POST /transcribe`
- **Parameters**:
  - `audio_file`: Audio file (multipart/form-data)
  - `language`: Language code (optional)
- **Response Example**:
```json
{
    "status": "success",
    "task_id": "uuid-task-id"
}
```

### 2. Transcribe from URL
- **Endpoint**: `POST /transcribe_url`
- **Parameters**:
```json
{
    "url": "Audio file URL",
    "language": "Language code (optional)"
}
```
- **Response Example**: Same as above

This is an asynchronous endpoint. The server immediately returns a task ID while processing the transcription in the background. Use the task ID to check the transcription status.

### 3. Check Task Status
- **Endpoint**: `GET /task/{task_id}`
- **Response Example**:
```json
{
    "status": "success",
    "data": {
        "id": "task-id",
        "status": "completed",
        "result": {
            "text": "Transcribed text content",
            "language": "Detected language",
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "Segment text"
                }
            ],
            "srt": "1\n00:00:00,000 --> 00:00:02,500\nSegment text"
        }
    }
}
```

The response now includes an additional `srt` field containing the transcription in SRT subtitle format, which can be used directly for video captioning.

### 4. List All Tasks
- **Endpoint**: `GET /tasks`
- **Returns**: Status and information for all tasks

## Docker Deployment

The project includes a Dockerfile for easy deployment:

```bash
docker build -f Dockerfile-whisper -t whisper . # do this first
docker build -t whisper-api .
docker run -p 8100:8100 whisper-api
```

## Docker Compose Deployment

For easier deployment and management, you can also use Docker Compose:

1. Make sure you have Docker and Docker Compose installed
2. Run the following command:
```bash
docker-compose up -d
```

This will build and start the Whisper API service, which will be accessible at http://localhost:8100

To stop the service:
```bash
docker-compose down
```

The Docker Compose configuration includes:
- Automatic GPU support (if available)
- Volume mounting for data persistence
- Proper environment configuration
- Automatic restart on failure (unless manually stopped)

## NAS Deployment Optimization

If you're deploying on a NAS device and experiencing network errors during build:

1. The optimized Dockerfile uses domestic mirror sources for faster downloads
2. Build steps are separated to reduce single-step load
3. Docker Compose configuration includes network optimizations
4. Consider increasing Docker resource limits on your NAS

## Important Notes

1. The service uses the "turbo" model by default. Other Whisper models can be configured in the code
2. Transcription tasks are processed asynchronously. Results must be retrieved using the task ID
3. Duplicate transcription tasks (based on MD5 hash) are automatically detected
4. Temporary files are automatically cleaned up after processing


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Support

If you encounter any problems or have questions, please [open an issue](issues).
