# 🎨 ComfyUI批量生图管理平台

> 企业级AI绘画批量处理系统 - 将ComfyUI API嫁接到您的平台，实现批量远程生图

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 核心特性

- 🚀 **批量任务处理** - 支持大规模图像批量生成
- 📊 **实时进度监控** - WebSocket实时更新任务状态
- 🌐 **Web管理界面** - 现代化的任务管理后台
- 🔗 **RESTful API** - 完整的API接口，易于集成
- 💾 **任务持久化** - SQLite数据库存储任务状态
- 🔧 **零配置启动** - 一个脚本解决所有部署问题
- 🎯 **多工作流支持** - 支持Qwen、FLUX、角色抠图等多种工作流

## 🎯 解决的核心问题

### ❌ 原始问题
- ComfyUI只能单个生图，不支持批量处理
- 存在CORS跨域限制，无法直接集成到Web平台
- 缺少任务队列管理和进度监控
- 没有统一的API接口

### ✅ 完美解决
- **批量生图引擎** - 支持同时处理数百个任务
- **CORS完全解决** - FastAPI服务器作为代理层
- **企业级任务管理** - 完整的任务生命周期管理
- **标准化API** - RESTful接口，支持多种编程语言集成

## 🚀 30秒快速启动

```bash
# 1. 克隆项目
git clone https://github.com/LukeChenug/comfyui-batch-generation-platform.git
cd comfyui-batch-generation-platform

# 2. 一键启动（自动安装依赖、配置环境、启动服务）
./quick_start.sh

# 3. 打开浏览器访问
# 管理界面: http://localhost:8001/batch_generation_dashboard.html
# API文档:  http://localhost:8001/docs
```

## 📦 项目结构

```
comfyui-batch-generation-platform/
├── batch_generation_dashboard.html    # 🌐 Web管理界面
├── comfyui_api_server.py              # ⚙️ 后端API服务器
├── comfyui_workflow_api.py            # 🔧 工作流API处理
├── api_examples.py                    # 📝 Python SDK示例
├── quick_start.sh                     # 🚀 一键启动脚本
├── requirements.txt                   # 📦 Python依赖
├── tasks.db                           # 🗃️ 任务数据库（自动创建）
├── generated_images/                  # 🖼️ 生成图片存储
├── uploaded_images/                  # 📤 上传图片存储
├── logs/                              # 📋 运行日志
├── Qwen-Image 文生图（API）.json      # 📄 Qwen工作流
├── Qwen-Edit 图生图 (API).json        # 📄 Qwen编辑工作流
└── 角色抠图_透明背景工作流（API）.json # 📄 角色抠图工作流
```

## 💡 使用场景

### 1. 儿童绘本批量生产
```python
from api_examples import ComfyUIBatchClient

client = ComfyUIBatchClient("http://localhost:8001")

# 批量生成绘本插图
story_prompts = [
    "两个小熊来到了森林中的一条小溪边",
    "小女孩在公园里放风筝",
    "一只可爱的小猫在花园里玩耍"
]

task_ids = client.submit_batch_tasks(story_prompts)
results = client.wait_for_batch(task_ids)
```

### 2. 电商产品图批量生成
```python
# 批量生成产品展示图
product_prompts = [
    f"Professional photo of {product}, white background, studio lighting"
    for product in ["coffee mug", "laptop bag", "smartphone case"]
]

task_ids = client.submit_batch_tasks(product_prompts, width=1024, height=1024)
```

### 3. 角色抠图批量处理
```python
# 批量处理角色抠图
client.submit_single_task(
    prompt="角色抠图",
    input_image="character.png",
    workflow_type="rembg"
)
```

## 🏗️ 系统架构

```
                    ┌─────────────────┐
                    │   用户平台/APP   │
                    └─────────┬───────┘
                              │ HTTP/WebSocket
                    ┌─────────▼───────┐
                    │  FastAPI服务器   │ ← 解决CORS问题
                    │  (批量任务管理)   │ ← 队列调度
                    └─────────┬───────┘
                              │ HTTP
                    ┌─────────▼───────┐
                    │ ComfyUI服务器    │ ← 您的现有服务器
                    │ (AI图像生成)     │
                    └─────────────────┘
```

## 📊 API 接口

### 提交单个任务
```bash
POST /generate
Content-Type: application/json

{
  "prompt": "两个小熊来到了森林中的一条小溪边",
  "negative_prompt": "ugly, blurry, low quality",
  "width": 784,
  "height": 496,
  "steps": 4,
  "cfg": 1,
  "batch_size": 1,
  "workflow_type": "qwen"
}
```

### 提交批量任务
```bash
POST /batch
Content-Type: application/json

{
  "requests": [
    {"prompt": "提示词1", ...},
    {"prompt": "提示词2", ...}
  ],
  "batch_name": "batch_001"
}
```

### 查询任务状态
```bash
GET /tasks
GET /task/{task_id}
```

### WebSocket 实时更新
```javascript
const ws = new WebSocket('ws://localhost:8001/ws');
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'task_update') {
    console.log('任务更新:', message.data);
  }
};
```

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代化Python Web框架
- **SQLite** - 任务数据持久化
- **WebSocket** - 实时双向通信
- **Asyncio** - 高性能异步处理

### 前端
- **原生JavaScript** - 无框架依赖
- **WebSocket客户端** - 实时更新
- **响应式设计** - 支持移动端

## 📈 功能特性

### ✅ 已实现
- [x] 批量任务提交和管理
- [x] 实时进度监控（WebSocket）
- [x] Web管理界面
- [x] 多工作流支持（Qwen、FLUX、角色抠图）
- [x] 图片上传和处理
- [x] 任务历史记录
- [x] 错误处理和重试
- [x] 批量生图（每个提示词生成多张图片）

### 🔄 计划中
- [ ] 用户认证系统
- [ ] 任务优先级管理
- [ ] 云存储集成（S3/OSS）
- [ ] 多ComfyUI服务器集群
- [ ] 高级调度算法

## 📖 文档

- [详细部署指南](README_批量生图平台.md)
- [使用指南](使用指南.md)
- [API示例代码](api_examples.py)

## 🐛 故障排除

### 常见问题

**1. CORS问题**
- ✅ 已通过FastAPI代理完全解决

**2. ComfyUI连接失败**
- 检查ComfyUI服务器地址和端口
- 确认网络连通性：`curl http://your-comfyui-server:8188`

**3. 任务一直处于Loading状态**
- 查看日志：`tail -f logs/api_server.log`
- 检查ComfyUI服务器是否正常运行

**4. 图片生成失败**
- 检查工作流JSON格式是否正确
- 确认ComfyUI服务器有足够的GPU资源

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 强大的AI图像生成工具
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架

---

⭐ 如果这个项目对你有帮助，请给个 Star！

