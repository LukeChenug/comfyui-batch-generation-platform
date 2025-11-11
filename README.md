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
- [故障排除快速参考](故障排除快速参考.md) - 网络连接和API配置问题快速解决方案

## 🐛 故障排除

### 网络连接和API配置问题

#### 1. API服务器地址配置问题

**问题现象：**
- 前端显示"API连接失败"
- 任务提交后无法获取状态
- 图片无法正常显示

**解决方案：**

**情况A：API服务器在本机运行**
- 使用 `http://localhost:8001`（默认配置）
- 确保API服务器正在运行：`python comfyui_api_server.py`

**情况B：API服务器在其他电脑上**
- 不能使用 `localhost`，需要使用实际IP地址
- 获取API服务器所在电脑的IP地址：
  ```bash
  # Windows
  ipconfig
  
  # Linux/Mac
  ifconfig
  ```
- 在Web界面中修改API服务器地址为：`http://192.168.x.x:8001`（替换为实际IP）

**情况C：从其他设备访问**
- 确保API服务器绑定到 `0.0.0.0`（已在代码中配置）
- 确保防火墙允许8001端口
- 使用局域网IP地址访问

**验证连接：**
```bash
# 测试API服务器是否可访问
curl http://localhost:8001/health

# 或使用浏览器访问
http://localhost:8001/docs
```

#### 2. Git连接GitHub失败

**问题现象：**
- `fatal: unable to access 'https://github.com/...': Recv failure: Connection was reset`
- `fatal: unable to access 'https://github.com/...': Failed to connect`

**解决方案：**

**方法1：配置HTTP代理（推荐）**
```bash
# 查看系统代理设置（通常在代理软件中查看）
# 常见代理地址：
# - Clash: http://127.0.0.1:7890
# - V2Ray: http://127.0.0.1:10809
# - SOCKS5: socks5://127.0.0.1:1080

# 配置Git使用代理
git config --global http.proxy http://127.0.0.1:你的代理端口
git config --global https.proxy http://127.0.0.1:你的代理端口

# 验证配置
git config --global --get http.proxy
git config --global --get https.proxy

# 测试连接
git fetch origin
```

**方法2：使用SSH方式（需要配置SSH密钥）**
```bash
git remote set-url origin git@github.com:用户名/仓库名.git
```

**方法3：清除代理配置**
```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

#### 3. ComfyUI服务器连接问题

**问题现象：**
- 任务提交后一直处于"生成中"状态
- 日志显示"连接ComfyUI服务器失败"
- 任务状态显示"连接失败，无法获取任务状态"

**解决方案：**

**检查1：ComfyUI服务器地址配置**
- 编辑 `comfyui_api_server.py`，检查以下配置：
  ```python
  COMFYUI_SERVER = "http://117.50.172.15:8188"  # 修改为你的ComfyUI服务器地址
  COMFYUI_WS = "ws://117.50.172.15:8188/ws"
  ```

**检查2：网络连通性**
```bash
# 测试ComfyUI服务器是否可访问
curl http://你的ComfyUI地址:8188/system_stats

# 或使用Python测试
python -c "import requests; r = requests.get('http://你的ComfyUI地址:8188/system_stats'); print(r.json())"
```

**检查3：连接超时和重试机制**
- 代码已实现自动重试机制（最多3次）
- 连接超时时间：连接10秒，读取60秒
- 如果连续失败10次，任务会标记为失败

**检查4：查看详细日志**
```bash
# Windows PowerShell
Get-Content logs\api_server.log -Tail 50

# Linux/Mac
tail -f logs/api_server.log
```

#### 4. 任务状态获取失败

**问题现象：**
- 任务提交成功，但显示"API连接失败，无法获取任务状态"
- 任务一直处于"generating"状态

**解决方案：**

**原因1：API端点路径错误（已修复）**
- 前端使用 `/status/{task_id}` 获取任务状态
- 确保API服务器端点正确：`GET /status/{task_id}`

**原因2：网络不稳定**
- 代码已实现自动重试机制
- 连续失败5次后才会停止轮询
- 失败后会自动增加重试延迟

**原因3：任务ID不匹配**
- 检查任务ID是否正确
- 查看浏览器控制台（F12）的错误信息

**调试方法：**
```javascript
// 在浏览器控制台（F12）中查看
// 1. 检查API服务器地址
console.log(manager.apiServer);

// 2. 测试连接
fetch('http://localhost:8001/health')
  .then(r => r.json())
  .then(console.log);

// 3. 查看任务状态
fetch('http://localhost:8001/status/任务ID')
  .then(r => r.json())
  .then(console.log);
```

#### 5. 图片无法显示（损坏状态）

**问题现象：**
- 任务显示"生成成功"，但图片无法显示
- 浏览器控制台显示图片加载失败
- 图片URL显示为相对路径

**解决方案：**

**原因：图片URL是相对路径**
- API返回的图片URL格式：`/images/filename.png`
- 前端需要拼接API服务器地址：`http://localhost:8001/images/filename.png`

**已实现的修复：**
- 前端已添加 `getImageUrl()` 函数自动转换URL
- 所有图片显示位置都已使用完整URL
- 支持相对路径和绝对路径自动识别

**验证方法：**
```javascript
// 在浏览器控制台检查图片URL
// 1. 查看任务数据
fetch('http://localhost:8001/status/任务ID')
  .then(r => r.json())
  .then(task => {
    console.log('图片URL:', task.result_urls);
    // 应该显示完整URL，如：http://localhost:8001/images/xxx.png
  });

// 2. 直接访问图片URL测试
// 在浏览器中打开：http://localhost:8001/images/文件名.png
```

**手动修复（如果仍有问题）：**
- 检查API服务器是否正常提供静态文件服务
- 确认 `generated_images` 目录存在且包含图片文件
- 检查文件权限

#### 6. 连接状态显示异常

**问题现象：**
- 状态显示"已连接"，但提交任务后显示"连接失败"
- 状态频繁在"已连接"和"连接失败"之间切换

**解决方案：**

**已实现的改进：**
- 初始化时先测试API连接
- 不会因单次失败立即标记为连接失败
- 连续失败3次后才标记为失败
- 失败后自动重连（5秒后）

**调试步骤：**
1. 打开浏览器控制台（F12）
2. 查看网络请求（Network标签）
3. 检查失败的请求和错误信息
4. 查看控制台日志中的连接测试结果

### 其他常见问题

**1. CORS问题**
- ✅ 已通过FastAPI CORS中间件完全解决
- 如果仍有问题，检查 `comfyui_api_server.py` 中的CORS配置

**2. 任务一直处于Loading状态**
- 查看日志：`tail -f logs/api_server.log`
- 检查ComfyUI服务器是否正常运行
- 检查网络连接是否稳定

**3. 图片生成失败**
- 检查工作流JSON格式是否正确
- 确认ComfyUI服务器有足够的GPU资源
- 查看ComfyUI服务器的错误日志

**4. 端口被占用**
```bash
# Windows
netstat -ano | findstr :8001

# Linux/Mac
lsof -i :8001

# 停止占用端口的进程
# Windows: taskkill /PID 进程ID /F
# Linux/Mac: kill -9 进程ID
```

**5. 依赖安装失败**
```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
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
curl http://localhost:8001/health

# 获取所有任务
curl http://localhost:8001/tasks

# 获取任务状态
curl http://localhost:8001/status/任务ID
```

**3. 浏览器开发者工具**
- 按F12打开开发者工具
- 查看Console标签的错误信息
- 查看Network标签的请求和响应
- 检查Application标签的localStorage数据

**4. 检查配置文件**
- `comfyui_api_server.py` - API服务器配置
- `batch_generation_dashboard.html` - 前端API地址配置
- 确保两处的地址配置一致

## 📝 技术问题记录

> 本文档记录开发过程中遇到的技术问题和解决方案，方便后续追溯和参考

### 2025-11-11 - 网络连接和API配置问题修复

**问题描述：**
1. API服务器连接失败 - 任务提交后无法获取状态
2. 图片无法显示 - 图片URL是相对路径，浏览器无法加载
3. Git连接GitHub失败 - 网络连接被重置
4. ComfyUI连接不稳定 - 任务处理过程中连接中断

**根本原因：**
- API端点路径错误：前端使用 `/task/{task_id}` 但后端是 `/status/{task_id}`
- 图片URL是相对路径 `/images/filename.png`，需要拼接API服务器地址
- Git未配置代理，无法访问GitHub
- HTTP请求缺少超时和重试机制，网络不稳定时容易失败

**解决方案：**
1. **修复API端点路径**
   - 前端：`/task/{task_id}` → `/status/{task_id}`
   - 文件：`batch_generation_dashboard.html`

2. **修复图片URL问题**
   - 添加 `getImageUrl()` 函数自动转换相对路径为完整URL
   - 修复所有图片显示位置（列表、详情、缩略图）
   - 文件：`batch_generation_dashboard.html`

3. **配置Git代理**
   - 添加HTTP代理配置支持
   - 创建代理配置脚本 `configure_git_proxy.ps1`
   - 支持HTTP/HTTPS和SOCKS5代理

4. **增强网络连接稳定性**
   - 为 `aiohttp.ClientSession` 添加超时配置（连接10秒，读取60秒）
   - 为所有HTTP请求添加重试机制（最多3次）
   - 任务状态轮询增加连续失败检测（最多10次）
   - 文件：`comfyui_api_server.py`

5. **改进前端连接检测**
   - 初始化时先测试API连接
   - 连续失败3次后才标记为连接失败
   - 失败后自动重连（5秒后）
   - 文件：`batch_generation_dashboard.html`

**相关文件：**
- `comfyui_api_server.py` - HTTP超时和重试机制
- `batch_generation_dashboard.html` - API端点修复、图片URL转换、连接检测改进
- `configure_git_proxy.ps1` - Git代理配置工具

**经验总结：**
- API端点路径必须前后端一致
- 相对路径需要根据运行环境转换为绝对路径
- 网络请求必须配置超时和重试机制
- 连接状态检测应该容忍临时失败，避免误报

### 2025-11-11 - 图片闪烁和尺寸变化问题修复

**问题描述：**
1. 轮询刷新时图片会闪烁 - 图片在刷新过程中会瞬间放大再缩小
2. 快速刷新浏览器时图片尺寸变化 - 每条任务列表的图片都会瞬间放大再缩小回原状态

**根本原因：**
- 图片容器使用 `height: auto`，在图片加载时容器尺寸会变化
- 缺少CSS containment优化，导致布局重排
- 图片加载前后容器尺寸不一致，触发浏览器重新计算布局
- 没有固定容器高度，导致图片加载时出现尺寸闪烁

**解决方案：**
1. **固定容器高度**
   - `.result-container .image-grid` 设置固定高度 `height: 500px`
   - 图片项设置 `height: 100%` 填充容器
   - 确保图片加载前后容器尺寸一致

2. **优化渲染性能**
   - 添加 `contain: layout style paint` 到图片容器和图片元素
   - 使用 `will-change: opacity` 优化透明度变化
   - 减少浏览器布局重排和重绘

3. **保存图片加载状态**
   - 刷新前保存已加载图片的状态（opacity、data-loaded属性）
   - 已加载图片直接显示，不触发过渡效果
   - 使用 `requestAnimationFrame` 立即显示已加载图片

4. **智能图片渲染**
   - `renderResultImages()` 接收 `existingImageState` 参数
   - 已加载图片直接设置为 `opacity: 1`，禁用过渡效果
   - 未加载图片保持原有淡入效果

**相关文件：**
- `batch_generation_dashboard.html` - CSS样式优化、图片渲染逻辑改进

**经验总结：**
- 图片容器应该设置固定高度，避免加载时尺寸变化
- 使用CSS containment可以显著减少布局重排
- 已加载的图片状态应该被保存和恢复，避免重复加载
- `will-change` 属性可以提示浏览器优化特定属性的变化

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 强大的AI图像生成工具
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架

---

⭐ 如果这个项目对你有帮助，请给个 Star！

