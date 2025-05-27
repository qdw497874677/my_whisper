# Whisper API Service

A REST API service for speech-to-text transcription powered by OpenAI's Whisper model. This service provides an easy-to-use interface for audio transcription with support for multiple languages.

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
            ]
        }
    }
}
```

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

## Important Notes

1. The service uses the "turbo" model by default. Other Whisper models can be configured in the code
2. Transcription tasks are processed asynchronously. Results must be retrieved using the task ID
3. Duplicate transcription tasks (based on MD5 hash) are automatically detected
4. Temporary files are automatically cleaned up after processing


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Support

If you encounter any problems or have questions, please [open an issue](issues).