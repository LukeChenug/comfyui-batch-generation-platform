import asyncio
import logging
import time
from typing import Dict, Optional, List
from dataclasses import dataclass
from pathlib import Path

from backend.src.engines.base import TaskStatus
from backend.src.engines.comfyui.adapter import ComfyUIAdapter
from backend.src.scenes.registry import scene_registry
from backend.src.database import db
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class JobContext:
    job_id: str
    scene_id: str
    user_input: Dict
    user_id: Optional[str] = None

class JobRunner:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.running = False
        self.current_job: Optional[JobContext] = None
        self.adapter = ComfyUIAdapter() 
        # TODO: 未来可以通过 EngineRouter 选择 Adapter

    async def start(self):
        """启动后台 Worker"""
        if self.running:
            return
        self.running = True
        logger.info("🚀 JobRunner started (Concurrency=1)")
        asyncio.create_task(self._worker_loop())

    async def stop(self):
        """停止 Worker"""
        self.running = False
        logger.info("🛑 JobRunner stopping...")

    def enqueue(self, job_context: JobContext):
        """提交任务到队列"""
        self.queue.put_nowait(job_context)
        logger.info(f"📥 Job enqueued: {job_context.job_id} (Queue size: {self.queue.qsize()})")

    async def _worker_loop(self):
        """消费者循环"""
        logger.info("Worker loop started")
        while self.running:
            try:
                # 等待任务 (带超时以便能响应停止信号)
                try:
                    job = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                self.current_job = job
                
                try:
                    await self._process_job(job)
                except Exception as e:
                    logger.error(f"❌ Job {job.job_id} failed: {e}", exc_info=True)
                    self._update_db(job.job_id, status="failed", error=str(e))
                finally:
                    self.current_job = None
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)

    async def _process_job(self, job: JobContext):
        logger.info(f"▶️ Processing job: {job.job_id}")
        
        # 1. Update Status: Running
        self._update_db(job.job_id, status="running", progress=10, message="正在准备场景...")
        
        # 2. Load Scene
        scene = scene_registry.get_scene(job.scene_id)
        if not scene:
            raise ValueError(f"Scene not found: {job.scene_id}")
            
        # 3. Compile Workflow
        try:
            workflow = scene.compile(job.user_input)
        except Exception as e:
            raise ValueError(f"Compilation failed: {e}")

        # 4. Preflight (Optional)
        # report = await self.adapter.preflight()
        
        # 5. Submit to Engine
        self._update_db(job.job_id, progress=20, message="提交到生成引擎...")
        engine_job_id = await self.adapter.run(workflow)
        logger.info(f"🔗 Engine Job ID: {engine_job_id}")

        # 6. Poll Status
        self._update_db(job.job_id, progress=30, message="等待生成...")
        
        # 简单轮询逻辑 (MVP)
        for i in range(300): # 10分钟超时
            if not self.running: 
                await self.adapter.cancel(engine_job_id)
                return

            status = await self.adapter.status(engine_job_id)
            
            if status == TaskStatus.COMPLETED:
                break
            elif status == TaskStatus.FAILED:
                raise RuntimeError("Engine reported failure")
            
            # 模拟进度 (Fake progress 30% -> 90%)
            if i % 5 == 0:
                fake_progress = 30 + min(60, i * 2)
                self._update_db(job.job_id, progress=fake_progress)
            
            await asyncio.sleep(2)
        else:
            raise TimeoutError("Job timed out")

        # 7. Get Results
        self._update_db(job.job_id, progress=95, message="下载结果...")
        local_files = await self.adapter.result(engine_job_id)
        
        # 8. Finish
        result_urls = [Path(p).name for p in local_files]
        
        self._update_db(
            job.job_id, 
            status="completed", 
            progress=100, 
            message="完成",
            result_url=result_urls[0] if result_urls else None,
            result_urls=result_urls
        )
        logger.info(f"✅ Job {job.job_id} completed!")

    def _update_db(self, task_id: str, **kwargs):
        """Helper to update DB"""
        task = db.get_task(task_id) or {"task_id": task_id}
        task.update(kwargs)
        if kwargs.get("status") in ["completed", "failed"]:
            task["completed_at"] = datetime.now().isoformat()
            
        db.save_task(task)
        
        # TODO: Trigger Websocket Broadcast

# Singleton
job_runner = JobRunner()

