import whisper
import os
import uuid
import asyncio
import json
import datetime
import sqlite3
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
import requests

class TranscribeUrlRequest(BaseModel):
    url: str
    language: Optional[str] = None
import tempfile
import hashlib

class Task(BaseModel):
    id: str
    audio_path: str
    model_size: str
    language: Optional[str]
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    file_hash: Optional[str] = None  # 添加文件哈希值

class State:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.db_file = "whisper_tasks.db"
        # 初始化数据库
        self._init_db()
        # 从数据库加载任务状态
        self._load_tasks()
    
    def _init_db(self) -> None:
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 创建任务表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            audio_path TEXT NOT NULL,
            model_size TEXT NOT NULL,
            language TEXT,
            status TEXT NOT NULL,
            result TEXT,
            error TEXT,
            timestamp TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_tasks(self) -> None:
        """从数据库加载任务状态"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, audio_path, model_size, language, status, result, error FROM tasks")
            rows = cursor.fetchall()
            
            for row in rows:
                task_id, audio_path, model_size, language, status, result_json, error = row
                
                # 解析JSON结果（如果有）
                result = json.loads(result_json) if result_json else None
                
                # 创建Task对象并存储在内存中
                task = Task(
                    id=task_id,
                    audio_path=audio_path,
                    model_size=model_size,
                    language=language,
                    status=status,
                    result=result,
                    error=error
                )
                self.tasks[task_id] = task
                
            conn.close()
        except Exception as e:
            print(f"Error loading tasks from database: {e}")
    
    def _save_task(self, task: Task) -> None:
        """将任务状态保存到数据库"""
        try:
            # 先更新内存中的任务状态
            self.tasks[task.id] = task
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 检查file_hash列是否存在，如果不存在则添加
            try:
                cursor.execute("SELECT file_hash FROM tasks LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE tasks ADD COLUMN file_hash TEXT")
                conn.commit()
            
            timestamp = datetime.datetime.now().isoformat()
            result_json = json.dumps(task.result) if task.result else None
            
            # 使用REPLACE策略插入/更新任务
            cursor.execute('''
            INSERT OR REPLACE INTO tasks (id, audio_path, model_size, language, status, result, error, timestamp, file_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id,
                task.audio_path,
                task.model_size,
                task.language,
                task.status,
                result_json,
                task.error,
                timestamp,
                task.file_hash  # 添加文件哈希值
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving task to database: {e}")
    
    def add_task(self, audio_path: str, model_size: str, language: Optional[str], file_hash: str = None) -> str:
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            audio_path=audio_path,
            model_size=model_size,
            language=language,
            status="pending",
            file_hash=file_hash  # 添加文件哈希值
        )
        self.tasks[task_id] = task
        
        # 将任务保存到数据库
        self._save_task(task)
        
        return task_id
    
    def find_same_task(self, file_hash: str, language: Optional[str]) -> Optional[str]:
        """查找具有相同音频文件哈希和语言参数的任务"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 先添加file_hash列（如果不存在）
            try:
                cursor.execute("ALTER TABLE tasks ADD COLUMN file_hash TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                # 列已存在，忽略错误
                pass
                
            # 查询相同哈希和语言的任务
            if language:
                cursor.execute("SELECT id FROM tasks WHERE file_hash = ? AND language = ?", 
                              (file_hash, language))
            else:
                cursor.execute("SELECT id FROM tasks WHERE file_hash = ? AND language IS NULL", 
                              (file_hash,))
                
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]  # 返回任务ID
            return None
            
        except Exception as e:
            print(f"Error finding same task: {e}")
            return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = status
            if result:
                task.result = result
            if error:
                task.error = error
            
            # 将更新后的任务状态保存到数据库
            self._save_task(task)
    
    def list_tasks(self) -> List[Task]:
        return list(self.tasks.values())

# 创建全局状态对象
state = State()

# 加载Whisper模型
model = whisper.load_model("turbo")

app = FastAPI(title="Whisper API", description="API for Whisper ASR", version="1.0")

def format_timestamp(seconds: float) -> str:
    """将秒数转换为SRT时间格式 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remaining = seconds % 60
    seconds_int = int(seconds_remaining)
    milliseconds = int((seconds_remaining - seconds_int) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds_int:02d},{milliseconds:03d}"

def generate_srt(segments: List[Dict[str, Any]]) -> str:
    """根据segments生成SRT字幕内容"""
    srt_lines = []
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp(segment["start"])
        end_time = format_timestamp(segment["end"])
        text = segment["text"].strip()
        
        srt_lines.extend([
            str(i),
            f"{start_time} --> {end_time}",
            text,
            ""  # 空行分隔
        ])
    
    # 移除最后的空行
    if srt_lines and srt_lines[-1] == "":
        srt_lines.pop()
        
    return "\n".join(srt_lines)

async def process_transcribe_task(task_id: str, file_path: str, language: Optional[str]):
    """异步处理转录任务"""
    try:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(
                executor,
                lambda: model.transcribe(
                    file_path,
                    language=language,
                    verbose=False
                )
            )
        
        # 格式化结果
        segments = [
            {
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"]
            }
            for segment in result["segments"]
        ]
        
        formatted_result = {
            "text": result["text"],
            "language": result["language"],
            "segments": segments,
            "srt": generate_srt(segments)  # 添加SRT字幕格式数据
        }
        
        state.update_task(task_id, "completed", result=formatted_result)
        
        # 删除临时文件
        try:
            os.unlink(file_path)
        except:
            pass
            
    except Exception as e:
        state.update_task(task_id, "failed", error=str(e))
        # 删除临时文件
        try:
            os.unlink(file_path)
        except:
            pass

async def download_video(url: str) -> tuple[str, bytes]:
    """
    从URL下载视频文件
    返回: (文件名, 文件内容)
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # 从URL或Content-Disposition header获取文件名
    content_disposition = response.headers.get('content-disposition')
    if content_disposition and 'filename=' in content_disposition:
        filename = content_disposition.split('filename=')[1].strip('"')
    else:
        # 从URL中提取文件名
        filename = url.split('/')[-1].split('?')[0]
        if not filename:
            filename = 'video.mp4'
    
    # 读取文件内容
    content = response.content
    return filename, content

@app.post("/transcribe_url", response_class=JSONResponse)
async def api_transcribe_url(request: TranscribeUrlRequest):
    """
    通过URL提交音频转录任务并返回任务ID。
    """
    try:
        # 下载视频文件
        filename, content = await download_video(request.url)
        
        # 计算文件的MD5哈希值
        file_hash = hashlib.md5(content).hexdigest()
        
        # 检查是否存在相同的任务
        existing_task_id = state.find_same_task(file_hash, request.language)
        if existing_task_id:
            existing_task = state.get_task(existing_task_id)
            if existing_task:
                return {
                    "status": "success",
                    "task_id": existing_task_id,
                    "message": "相同的任务已经存在"
                }
        
        # 保存下载的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        # 创建新任务，并存储文件哈希值
        task_id = state.add_task(temp_path, "turbo", request.language, file_hash=file_hash)
        
        # 异步执行转录任务
        asyncio.create_task(process_transcribe_task(
            task_id=task_id,
            file_path=temp_path,
            language=request.language
        ))
        
        return {"status": "success", "task_id": task_id}
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"无法下载视频: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe", response_class=JSONResponse)
async def api_transcribe(
    audio_file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="Optional language specification")
):
    """
    提交音频转录任务并返回任务ID。
    如果存在相同的任务，则直接返回该任务ID。
    """
    temp_path = None
    try:
        # 读取文件内容
        content = await audio_file.read()
        
        # 计算文件的MD5哈希值
        file_hash = hashlib.md5(content).hexdigest()
        
        # 检查是否存在相同的任务
        existing_task_id = state.find_same_task(file_hash, language)
        if existing_task_id:
            existing_task = state.get_task(existing_task_id)
            if existing_task:
                return {
                    "status": "success", 
                    "task_id": existing_task_id,
                    "message": "相同的任务已经存在"
                }
        
        # 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        
        # 创建新任务，并存储文件哈希值
        task_id = state.add_task(temp_path, "turbo", language, file_hash=file_hash)
        
        # 异步执行转录任务
        asyncio.create_task(process_transcribe_task(
            task_id=task_id,
            file_path=temp_path,
            language=language
        ))
        
        return {"status": "success", "task_id": task_id}
        
    except Exception as e:
        # 确保清理临时文件
        if temp_path:
            try:
                os.unlink(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/{task_id}", response_class=JSONResponse)
async def get_task_status(task_id: str):
    """
    获取特定任务的状态。
    """
    task = state.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    response = {
        "status": "success",
        "data": {
            "id": task.id,
            "status": task.status
        }
    }
    
    if task.status == "completed" and task.result:
        response["data"]["result"] = task.result
    elif task.status == "failed" and task.error:
        response["data"]["error"] = task.error
    
    return response

@app.get("/tasks", response_class=JSONResponse)
async def list_all_tasks():
    """
    列出所有转录任务及其状态。
    """
    tasks = state.list_tasks()
    return {"status": "success", "data": tasks}

def start_api():
    # asyncio.set_event_loop(asyncio.DefaultEventLoopPolicy())
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)

    uvicorn.run(app, host="0.0.0.0", port=8100)

if __name__ == "__main__":
    print("Starting Whisper API server...")
    start_api()
