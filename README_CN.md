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

这是一个异步接口。服务器会立即返回任务ID，同时在后台处理转录任务。使用任务ID来查询转录状态。

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
            ],
            "srt": "1\n00:00:00,000 --> 00:00:02,500\n分段文本"
        }
    }
}
```

返回结果现在包含一个额外的`srt`字段，其中包含SRT字幕格式的转写内容，可直接用于视频字幕。

### 4. 获取所有任务列表
- **接口**：`GET /tasks`
- **返回**：所有任务的状态和信息

## Docker部署

项目提供了Dockerfile，可以直接构建Docker镜像：

```bash
docker build -f Dockerfile-whisper -t whisper . # 先构建whisper基础镜像
docker build -t whisper-api .
docker run -p 8100:8100 whisper-api
```

## Docker Compose部署

为了更简单的部署和管理，您也可以使用Docker Compose：

1. 确保您已安装Docker和Docker Compose
2. 运行以下命令：
```bash
docker-compose up -d
```

这将构建并启动Whisper API服务，您可以通过 http://localhost:8100 访问

停止服务：
```bash
docker-compose down
```

Docker Compose配置包括：
- 自动GPU支持（如果可用）
- 数据持久化卷挂载
- 正确的环境配置
- 失败自动重启功能（除非手动停止）

## NAS部署优化

如果您在NAS设备上部署时遇到网络错误：

1. 优化后的Dockerfile使用了国内镜像源以加快下载速度
2. 构建步骤已分离以减少单步负载
3. Docker Compose配置包含了网络优化
4. 建议增加NAS上Docker的资源限制

## 注意事项

1. 服务默认使用"turbo"模型，可以根据需要在代码中修改使用其他Whisper模型
2. 转写任务异步处理，需要通过任务ID查询结果
3. 相同音频文件（基于MD5哈希）的转写任务会自动去重
4. 临时文件会在处理完成后自动删除

## 许可证

[添加许可证信息]
