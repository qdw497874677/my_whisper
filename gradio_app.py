import gradio as gr
import requests
import os
import tempfile
import time
from typing import Optional

# API服务器地址
API_BASE_URL = "http://localhost:8100"

def transcribe_audio(audio_file: Optional[str], language: Optional[str] = None) -> str:
    """
    通过上传音频文件进行转录
    """
    if audio_file is None:
        return "请上传音频文件"
    
    try:
        with open(audio_file, 'rb') as f:
            files = {'audio_file': (os.path.basename(audio_file), f, 'audio/mpeg')}
            data = {}
            if language:
                data['language'] = language
            
            response = requests.post(f"{API_BASE_URL}/transcribe", files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            task_id = result['task_id']
            
            # 轮询任务状态直到完成
            return poll_task_status(task_id)
    except Exception as e:
        return f"转录过程中出错: {str(e)}"

def transcribe_url(url: str, language: Optional[str] = None) -> str:
    """
    通过URL进行音频转录
    """
    if not url:
        return "请提供音频文件的URL"
    
    try:
        payload = {"url": url}
        if language:
            payload["language"] = language
            
        response = requests.post(f"{API_BASE_URL}/transcribe_url", json=payload)
        response.raise_for_status()
        
        result = response.json()
        task_id = result['task_id']
        
        # 轮询任务状态直到完成
        return poll_task_status(task_id)
    except Exception as e:
        return f"转录过程中出错: {str(e)}"

def poll_task_status(task_id: str) -> str:
    """
    轮询任务状态直到完成
    """
    max_attempts = 30  # 最多尝试30次
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{API_BASE_URL}/task/{task_id}")
            response.raise_for_status()
            
            result = response.json()
            task_data = result['data']
            status = task_data['status']
            
            if status == 'completed':
                # 返回转录结果
                transcription = task_data['result']['text']
                srt_content = task_data['result'].get('srt', '')
                
                output = f"转录结果:\n{transcription}\n\n"
                if srt_content:
                    output += f"SRT字幕:\n{srt_content}"
                
                return output
            elif status == 'failed':
                error = task_data.get('error', '未知错误')
                return f"转录失败: {error}"
            else:
                # 任务仍在处理中
                attempt += 1
                time.sleep(2)  # 等待2秒后重试
                
        except Exception as e:
            attempt += 1
            time.sleep(2)
    
    return "任务处理超时，请稍后查看任务状态"

def list_tasks() -> str:
    """
    列出所有任务
    """
    try:
        response = requests.get(f"{API_BASE_URL}/tasks")
        response.raise_for_status()
        
        result = response.json()
        tasks = result['data']
        
        if not tasks:
            return "没有找到任务"
        
        output = "任务列表:\n"
        for task in tasks:
            output += f"ID: {task['id']}, 状态: {task['status']}\n"
        
        return output
    except Exception as e:
        return f"获取任务列表时出错: {str(e)}"

# 创建Gradio界面
with gr.Blocks(title="Whisper音频转录") as demo:
    gr.Markdown("# Whisper音频转录服务")
    gr.Markdown("使用Whisper模型将音频文件转录为文本")
    
    with gr.Tab("上传音频文件"):
        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(label="上传音频文件", type="filepath")
                language_input1 = gr.Textbox(label="语言 (可选)", placeholder="例如: zh, en")
                transcribe_btn = gr.Button("开始转录")
            with gr.Column():
                transcription_output1 = gr.Textbox(label="转录结果", lines=10, interactive=False)
        
        transcribe_btn.click(
            fn=transcribe_audio,
            inputs=[audio_input, language_input1],
            outputs=transcription_output1
        )
    
    with gr.Tab("通过URL转录"):
        with gr.Row():
            with gr.Column():
                url_input = gr.Textbox(label="音频文件URL", placeholder="https://example.com/audio.mp3")
                language_input2 = gr.Textbox(label="语言 (可选)", placeholder="例如: zh, en")
                transcribe_url_btn = gr.Button("开始转录")
            with gr.Column():
                transcription_output2 = gr.Textbox(label="转录结果", lines=10, interactive=False)
        
        transcribe_url_btn.click(
            fn=transcribe_url,
            inputs=[url_input, language_input2],
            outputs=transcription_output2
        )
    
    with gr.Tab("任务列表"):
        with gr.Row():
            with gr.Column():
                refresh_btn = gr.Button("刷新任务列表")
            with gr.Column():
                tasks_output = gr.Textbox(label="任务列表", lines=15, interactive=False)
        
        refresh_btn.click(
            fn=list_tasks,
            inputs=[],
            outputs=tasks_output
        )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
