# Whisper API Service

基于OpenAI Whisper模型的语音转写API服务，提供简单易用的REST API接口进行音频文件的转写服务。

## Docker 快速启动

```bash
docker run -p 8100:8100 hipc/whisper-api
```

访问API地址：http://localhost:8100

## 功能特点

- 支持音频文件上传转写
- 支持音频URL转写
- 异步处理转写任务
- 支持任务状态查询
- 支持指定音频语言
- 基于文件哈希的任务去重
- 使用SQLite持久化存储任务信息

## 环境要求

- Python 3.8+
- FFmpeg（用于音频处理）
- CUDA支持（可选，用于GPU加速）

## 安装说明

1. 克隆项目：
```bash
git clone [项目地址]
cd whisper-api
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 启动服务：
```bash
python main.py
```

默认服务将在 http://localhost:8100 启动

## API接口说明

### 1. 上传音频文件转写
- **接口**：`POST /transcribe`
- **参数**：
  - `audio_file`：音频文件（multipart/form-data）
  - `language`：语言代码（可选）
- **返回示例**：
```json
{
    "status": "success",
    "task_id": "uuid-task-id"
}
```

### 2. URL音频转写
- **接口**：`POST /transcribe_url`
- **参数**：
```json
{
    "url": "音频文件URL",
    "language": "语言代码（可选）"
}
```
- **返回示例**：同上

### 3. 查询任务状态
- **接口**：`GET /task/{task_id}`
- **返回示例**：
```json
{
    "status": "success",
    "data": {
        "id": "task-id",
        "status": "completed",
        "result": {
            "text": "转写文本内容",
            "language": "检测到的语言",
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "分段文本"
                }
            ]
        }
    }
}
```

### 4. 获取所有任务列表
- **接口**：`GET /tasks`
- **返回**：所有任务的状态和信息

## Docker部署

项目提供了Dockerfile，可以直接构建Docker镜像：

```bash
docker build -t whisper . 
docker build -t whisper-api .
docker run -p 8100:8100 whisper-api
```

## 注意事项

1. 服务默认使用"turbo"模型，可以根据需要在代码中修改使用其他Whisper模型
2. 转写任务异步处理，需要通过任务ID查询结果
3. 相同音频文件（基于MD5哈希）的转写任务会自动去重
4. 临时文件会在处理完成后自动删除

## 许可证

[添加许可证信息]