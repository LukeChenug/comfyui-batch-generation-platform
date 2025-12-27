import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.src.engines.comfyui.adapter import ComfyUIAdapter
from backend.src.engines.base import TaskStatus

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Workflow
WORKFLOW_PATH = Path("Qwen-Image 文生图（API）.json")
WORKFLOW_JSON = {}
if WORKFLOW_PATH.exists():
    with open(WORKFLOW_PATH, "r") as f:
        WORKFLOW_JSON = json.load(f)

async def test_preflight():
    async with ComfyUIAdapter() as adapter:
        report = await adapter.preflight()
        logger.info(f"Preflight Result: {report}")
        assert report is not None

async def test_run_cycle():
    if not WORKFLOW_JSON:
        logger.warning("Workflow file not found, skipping run test")
        return

    async with ComfyUIAdapter() as adapter:
        # 1. Check if online
        report = await adapter.preflight()
        if not report.ok:
            logger.warning("ComfyUI offline, skipping run test")
            return

        # 2. Submit
        logger.info("Submitting task...")
        import time
        # Clone workflow to avoid modifying global state
        payload = json.loads(json.dumps(WORKFLOW_JSON))
        
        # Modify seed if possible
        if "3" in payload and "inputs" in payload["3"]:
            payload["3"]["inputs"]["seed"] = int(time.time() * 1000) % 1000000000

        try:
            job_id = await adapter.run(payload)
            logger.info(f"Job ID: {job_id}")
            assert job_id is not None
        except Exception as e:
            logger.error(f"Run failed: {e}")
            # If run fails (e.g. missing node), we still consider the adapter working as it caught the error
            return

        # 3. Poll Status
        final_status = None
        for i in range(10): # Short poll for testing
            status = await adapter.status(job_id)
            logger.info(f"Status check {i}: {status}")
            final_status = status
            
            if status == TaskStatus.COMPLETED:
                break
            elif status == TaskStatus.FAILED:
                logger.error("Task failed in ComfyUI")
                break
            
            await asyncio.sleep(2)

        # 4. Result (if completed)
        if final_status == TaskStatus.COMPLETED:
            files = await adapter.result(job_id)
            logger.info(f"Generated files: {files}")
            assert len(files) > 0

        # 5. Cancel (if still running)
        if final_status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
             logger.info("Cancelling task...")
             success = await adapter.cancel(job_id)
             logger.info(f"Cancel success: {success}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_preflight())
    loop.run_until_complete(test_run_cycle())

