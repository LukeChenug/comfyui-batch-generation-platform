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
- 🔐 **用户认证系统** - 支持 API Key 访问控制和资源隔离
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
- **多用户支持** - 简单的 API Key 认证机制

## 🚀 30秒快速启动

```bash
# 1. 克隆项目
git clone https://github.com/LukeChenug/comfyui-batch-generation-platform.git
cd comfyui-batch-generation-platform

# 2. 一键启动（自动安装依赖、配置环境、启动服务）
./quick_start.sh

# 3. 打开浏览器访问
# 管理界面: http://localhost:8088/batch_generation_dashboard.html
# API文档:  http://localhost:8088/docs
```

## 📦 项目结构

```
comfyui-batch-generation-platform/
├── batch_generation_dashboard.html    # 🌐 Web管理界面
├── backend/                           # ⚙️ 后端服务目录
│   ├── src/
│   │   ├── main.py                    # 🚀 应用入口
│   │   ├── routes/                    # 🛣️ API路由
│   │   ├── services/                  # 🧠 业务逻辑
│   │   ├── adapters/                  # 🔌 外部适配器 (ComfyUI, S3等)
│   │   └── database/                  # 🗄️ 数据库操作
│   │   └── auth.py                    # 🔐 认证模块
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

client = ComfyUIBatchClient("http://localhost:8088")

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
                              │ HTTP/WebSocket (Auth: Bearer <API_KEY>)
                    ┌─────────▼───────┐
                    │  FastAPI服务器   │ ← 解决CORS问题
                    │  (批量任务管理)   │ ← 队列调度 / 用户认证
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
Authorization: Bearer <YOUR_API_KEY>

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
Authorization: Bearer <YOUR_API_KEY>

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
GET /status/{task_id}
Authorization: Bearer <YOUR_API_KEY>
```

### WebSocket 实时更新
```javascript
const ws = new WebSocket('ws://localhost:8088/ws?token=<YOUR_API_KEY>');
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
- [x] 用户认证系统 (API Key)

### 🔄 计划中
- [ ] 任务优先级管理
- [ ] 云存储集成 (S3/OSS)
- [ ] Serverless 架构迁移 (Vercel + ComfyDeploy)
- [ ] 高级调度算法

## 📖 文档

- [产品路线图](product_roadmap_mvp.md)
- [使用指南](使用指南.md)
- [API示例代码](api_examples.py)

## 🐛 故障排除

### 网络连接和API配置问题

#### 1. API服务器地址配置问题

**问题现象：**
- 前端显示"API连接失败"
- 任务提交后无法获取状态
- 图片无法正常显示

**解决方案：**

**情况A：API服务器在本机运行**
- 使用 `http://localhost:8088`（默认配置）
- 确保API服务器正在运行：`python -m backend.src.main`

**情况B：API服务器在其他电脑上**
- 不能使用 `localhost`，需要使用实际IP地址
- 获取API服务器所在电脑的IP地址：
  ```bash
  # Windows
  ipconfig
  
  # Linux/Mac
  ifconfig
  ```
- 在Web界面中修改API服务器地址为：`http://192.168.x.x:8088`（替换为实际IP）

**验证连接：**
```bash
# 测试API服务器是否可访问
curl http://localhost:8088/health

# 或使用浏览器访问
http://localhost:8088/docs
```

#### 2. ComfyUI服务器连接问题

**问题现象：**
- 任务提交后一直处于"生成中"状态
- 日志显示"连接ComfyUI服务器失败"

**解决方案：**

**检查1：ComfyUI服务器地址配置**
- 编辑 `backend/src/config/settings.py` (或环境变量)，检查配置。

**检查2：网络连通性**
```bash
# 测试ComfyUI服务器是否可访问
curl http://你的ComfyUI地址:8188/system_stats
```

**检查3：连接超时和重试机制**
- 代码已实现自动重试机制（最多3次）
- 连接超时时间：连接10秒，读取60秒

**检查4：查看详细日志**
```bash
# Windows PowerShell
Get-Content logs\api_server.log -Tail 50

# Linux/Mac
tail -f logs/api_server.log
```

#### 3. 任务状态获取失败（HTTP 404错误）

**问题现象：**
- 任务提交成功，但显示"API连接失败，无法获取任务状态"
- 错误信息：`HTTP 404: 获取任务状态失败`

**解决方案：**

**原因1：运行了错误的API服务器（最常见）**
- 确保运行的是 `python -m backend.src.main` 而不是旧的脚本。

**快速诊断：**
```bash
# 检查API文档标题
curl -s http://localhost:8088/docs | grep -i "title"
# 正确应该显示：ComfyUI批量生图API
```

**修复步骤：**
```bash
# 1. 停止所有API服务器进程
# Windows
taskkill /F /IM python.exe

# 2. 启动正确的API服务器
./quick_start.sh
```

#### 4. 图片无法显示（损坏状态）

**问题现象：**
- 任务显示"生成成功"，但图片无法显示
- 图片URL显示为相对路径

**解决方案：**

**已实现的修复：**
- 前端已添加 `getImageUrl()` 函数自动转换URL
- 所有图片显示位置都已使用完整URL `http://localhost:8088/images/xxx.png`

**验证方法：**
```javascript
// 在浏览器控制台检查图片URL
fetch('http://localhost:8088/status/任务ID')
  .then(r => r.json())
  .then(task => {
    console.log('图片URL:', task.result_urls);
  });
```

#### 5. 端口被占用
```bash
# Windows
netstat -ano | findstr :8088

# Linux/Mac
lsof -i :8088

# 停止占用端口的进程
# Windows: taskkill /PID 进程ID /F
# Linux/Mac: kill -9 进程ID
```

### 调试技巧

**1. 查看API服务器日志**
```bash
# Windows PowerShell
Get-Content logs\api_server.log -Tail 100 -Wait

# Linux/Mac
tail -f logs/api_server.log
```

**2. 测试API端点**
```bash
# 健康检查
curl http://localhost:8088/health

# 获取所有任务 (需 Auth Header)
curl -H "Authorization: Bearer sk-admin-123456" http://localhost:8088/tasks
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 强大的AI图像生成工具
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架

---

⭐ 如果这个项目对你有帮助，请给个 Star！
