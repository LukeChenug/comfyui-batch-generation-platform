import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import time

logger = logging.getLogger(__name__)

class SceneCompiler:
    @staticmethod
    def compile(template: Dict, mapping: Dict, user_input: Dict) -> Dict:
        """
        将用户输入编译为 ComfyUI Workflow Payload
        """
        # 深拷贝模板，避免修改原始对象
        workflow = json.loads(json.dumps(template))
        
        # 1. 处理简单映射 (Direct Value Injection)
        simple_map = mapping.get("simple", {})
        for input_key, path_list in simple_map.items():
            if input_key in user_input:
                value = user_input[input_key]
                SceneCompiler._set_value_by_path(workflow, path_list, value)
            elif input_key == "seed" and "seed" not in user_input:
                # 自动注入随机种子
                seed = int(time.time() * 1000) % 1000000000
                SceneCompiler._set_value_by_path(workflow, path_list, seed)

        # 2. 处理复杂映射 (Converters)
        complex_map = mapping.get("complex", {})
        for input_key, rule in complex_map.items():
            if input_key in user_input:
                value = user_input[input_key]
                converter_name = rule.get("converter")
                target_path = rule.get("target")
                
                if hasattr(SceneCompiler, converter_name):
                    converter = getattr(SceneCompiler, converter_name)
                    # Converter 返回一个 dict，我们需要把这个 dict merge 到 target path
                    result_dict = converter(value)
                    target_node = SceneCompiler._get_value_by_path(workflow, target_path)
                    if target_node and isinstance(target_node, dict):
                        target_node.update(result_dict)
                else:
                    logger.warning(f"Unknown converter: {converter_name}")

        return workflow

    @staticmethod
    def _set_value_by_path(data: Dict, path: List[str], value: Any):
        current = data
        for key in path[:-1]:
            current = current.get(key, {})
        current[path[-1]] = value

    @staticmethod
    def _get_value_by_path(data: Dict, path: List[str]) -> Any:
        current = data
        for key in path:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    # --- Converters ---
    
    @staticmethod
    def aspect_ratio_to_dims_sd3(ratio: str) -> Dict[str, int]:
        # SD3 推荐分辨率
        # 1024*1024 = 1048576 pixels
        mapping = {
            "1:1": {"width": 1024, "height": 1024},
            "4:3": {"width": 1152, "height": 896},
            "3:4": {"width": 896, "height": 1152},
            "16:9": {"width": 1344, "height": 768},
            "9:16": {"width": 768, "height": 1344}
        }
        return mapping.get(ratio, {"width": 1024, "height": 1024})


class Scene:
    def __init__(self, path: Path):
        self.path = path
        self.id = path.name
        self.schema = self._load_json("schema.json")
        self.template = self._load_json("template.json")
        self.manifest = self._load_json("manifest.json")
        
        # 覆盖 id 以 schema 为准
        if "id" in self.schema:
            self.id = self.schema["id"]

    def _load_json(self, filename: str) -> Dict:
        file_path = self.path / filename
        if not file_path.exists():
            logger.warning(f"Missing file in scene {self.id}: {filename}")
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def compile(self, user_input: Dict) -> Dict:
        mapping = self.schema.get("mapping", {})
        return SceneCompiler.compile(self.template, mapping, user_input)


class SceneRegistry:
    def __init__(self):
        self.scenes: Dict[str, Scene] = {}
        self.base_path = Path(__file__).parent
        self.reload()

    def reload(self):
        self.scenes = {}
        # 遍历子目录
        for item in self.base_path.iterdir():
            if item.is_dir() and (item / "schema.json").exists():
                try:
                    scene = Scene(item)
                    self.scenes[scene.id] = scene
                    logger.info(f"Loaded scene: {scene.id}")
                except Exception as e:
                    logger.error(f"Failed to load scene {item.name}: {e}")

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        return self.scenes.get(scene_id)

    def list_scenes(self) -> List[Dict]:
        return [
            {
                "id": s.id,
                "meta": s.schema.get("meta", {}),
                "ui_schema": s.schema.get("ui_schema", {})
            }
            for s in self.scenes.values()
        ]

# Global Instance
scene_registry = SceneRegistry()

