import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.src.scenes.registry import scene_registry, SceneCompiler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_registry_loading():
    scene_registry.reload()
    scenes = scene_registry.list_scenes()
    logger.info(f"Loaded Scenes: {[s['id'] for s in scenes]}")
    
    assert len(scenes) > 0
    assert "storybook" in [s['id'] for s in scenes]
    
    scene = scene_registry.get_scene("storybook")
    assert scene is not None
    assert scene.schema["id"] == "storybook"

def test_compiler_logic():
    scene = scene_registry.get_scene("storybook")
    assert scene is not None
    
    user_input = {
        "prompt": "A cute cat",
        "aspect_ratio": "16:9",
        "batch_size": 2
    }
    
    workflow = scene.compile(user_input)
    
    # 验证 Prompt 注入
    # Node 6 inputs text
    assert workflow["6"]["inputs"]["text"] == "A cute cat"
    
    # 验证 Seed 自动注入 (用户没传)
    assert isinstance(workflow["3"]["inputs"]["seed"], int)
    
    # 验证 Converter (16:9 -> 1344x768)
    # Node 58 inputs width/height
    assert workflow["58"]["inputs"]["width"] == 1344
    assert workflow["58"]["inputs"]["height"] == 768
    
    # 验证简单映射
    assert workflow["58"]["inputs"]["batch_size"] == 2

if __name__ == "__main__":
    test_registry_loading()
    test_compiler_logic()
    print("All Scene tests passed!")

