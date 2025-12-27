# Runner · MVP 阶段实现计划 (MVP Implementation Plan)

> **目标**：在 **不引入** 云算力、多用户、复杂调度的前提下，验证 Runner 能为创作者提供稳定、可复现的生产体验。
> **原则**：MVP 只解决“稳定产出”一个问题，不做任何越界功能。

---

## 一、MVP 功能边界 (Scope Boundary)

| 维度 | ✅ MVP 必须做 (Must Have) | ❌ MVP 明确不做 (Out of Scope) |
| :--- | :--- | :--- |
| **入口** | **Scene-first** (产品仅暴露场景) | Workflow 列表 / 节点编辑器 |
| **引擎** | **Local ComfyUI** (HTTP API) | 云算力 / GPU 托管 / 多引擎并发 |
| **调度** | **单机串行** (Concurrency = 1) | Redis / 分布式队列 / 复杂优先级 |
| **稳定** | **Preflight** (最小可运行验证) | 自动安装依赖 / 智能纠错 |
| **结果** | **本地存储 + ZIP 导出** | 对象存储 / 在线画廊 / 社区分享 |
| **用户** | **单机单用户** | 登录注册 / 权限管理 / 团队协作 |

---

## 二、功能模块拆解 (Module Breakdown)

### 🧩 模块 1：Scene System (场景系统)
*   **定位**：产品的唯一入口，彻底屏蔽底层图逻辑。
*   **首发场景**：
    1.  📖 **Storybook** (绘本模式)：慢而稳，注重一致性。
    2.  🎨 **Concept** (概念模式)：快而爽，注重灵感发散。
*   **Scene 结构**：
    *   `schema.json`: 定义 UI 表单 (JSON Schema)。
    *   `guardrails`: 参数白名单与范围约束 (防止 OOM)。
    *   `compiler`: 将用户意图 (Intent) 编译为引擎 Payload。
    *   `manifest`: 依赖声明 (模型/节点)。

### ⚙️ 模块 2：Engine Layer (引擎层)
*   **核心引擎**：ComfyUI (Local)。
*   **Adapter 职责**：
    *   提交 Graph JSON。
    *   轮询任务状态 (Polling)。
    *   下载生成图片 (Result Fetching)。
    *   **错误翻译**：将 ComfyUI 的 traceback 转换为用户可读的中文提示。

### 🩺 模块 3：Preflight (起飞前检查)
*   **核心职责**：在任务开始前拦截错误。
*   **检查项**：
    1.  🔌 **连接性**：ComfyUI 是否在线。
    2.  🏃 **可运行性**：核心模型是否存在。
    3.  📢 **人话报错**：明确告知“缺什么”。

### 🏃 模块 4：Job Runner (执行系统)
*   **核心约束**：**严格串行 (Concurrency = 1)**，保护显存。
*   **状态机**：`Pending` → `Running` → `Done` / `Failed` / `Cancelled`。
*   **容错**：任务失败必须有明确原因记录。

### 🖥️ 模块 5：Web UI (交互层)
*   **页面清单**：
    1.  **Scene List**: 场景选择页。
    2.  **Scene Detail**: 参数配置表单 (Schema 驱动)。
    3.  **Jobs**: 任务列表与状态监控。
    4.  **Results**: 结果预览与 ZIP 导出。

---

## 三、技术架构 (Architecture Subset)

```mermaid
graph TD
    UI[Web UI] <-->|REST + SSE| Server[Local Server]
    
    subgraph "Local Server"
        Scene[Scene Registry]
        Job[Job Runner (Serial)]
        Pre[Preflight]
        Adapter[ComfyUI Adapter]
        Store[Local Storage]
    end
    
    Server --> Scene
    Server --> Job
    Job --> Pre
    Job --> Adapter
    Adapter <-->|HTTP| Comfy[Local ComfyUI]
    Job --> Store
```

---

## 四、工程落地指南 (Implementation Guide)

### 📂 4.1 目录结构 (MVP Frozen)

> ⚠️ **注意**：MVP 阶段严禁随意新增顶层目录。

```text
runner/
├── apps/
│   ├── web/                  # 前端 (React)
│   └── local-server/         # 后端 (FastAPI)
│       ├── src/
│       │   ├── scenes/       # [核心] 场景包
│       │   │   ├── storybook/
│       │   │   └── concept/
│       │   ├── engines/      # [核心] 适配器
│       │   │   └── comfyui/
│       │   ├── jobs/         # [核心] 队列与状态
│       │   ├── routes/       # API 路由
│       │   └── storage/      # 文件操作
│       └── package.json
```

### 🔌 4.2 API 契约 (Minimum Contract)

| 资源 | 方法 | 路径 | 描述 |
| :--- | :--- | :--- | :--- |
| **Scenes** | `GET` | `/scenes` | 获取场景列表 |
| | `GET` | `/scenes/:id` | 获取场景详情 (Schema) |
| **Engine** | `POST` | `/engine/preflight` | 执行环境检查 |
| **Jobs** | `POST` | `/jobs` | 提交任务 |
| | `GET` | `/jobs/:id` | 获取任务详情 |
| | `GET` | `/jobs/stream` | SSE 全局状态流 |
| | `POST` | `/jobs/:id/cancel` | 取消任务 |

### 📅 4.3 开发阶段规划 (Phases)

#### Phase 0: 准备 (Setup)
*   [ ] 固定一套 ComfyUI Golden Setup (模型/插件)。
*   [ ] 准备最小测试 Workflow (文生图)。

#### Phase 1: 引擎先行 (Engine First)
*   [ ] 实现 `ComfyUIAdapter.run()`。
*   [ ] 实现结果图片拉取与本地保存。
*   [ ] 实现最小 Preflight (连接测试)。
*   **🎯 里程碑**：代码能跑通“文生图”流程。

#### Phase 2: 场景核心 (Scene Core)
*   [ ] 实现 Storybook Scene 包结构。
*   [ ] 实现 `SceneRegistry` 加载逻辑。
*   [ ] 实现 `Compiler` (Intent → Graph)。

#### Phase 3: 任务调度 (Job Runner)
*   [ ] 实现 `asyncio.Queue` 串行队列。
*   [ ] 完善状态机流转。
*   [ ] 错误捕获与日志记录。

#### Phase 4: 前端交互 (UI Integration)
*   [ ] 实现动态表单渲染。
*   [ ] 对接 SSE 实时状态。
*   [ ] 结果展示与 ZIP 打包。

---

## 五、验收标准 (Definition of Done)

只有同时满足以下条件，MVP 才算完成：

1.  ✅ **稳定性**：能连续稳定生成 10 页绘本插图无报错。
2.  ✅ **复现性**：同一组参数重复运行，结果完全一致。
3.  ✅ **拦截率**：Preflight 能拦截并提示“ComfyUI 未启动”或“模型缺失”。
4.  ✅ **黑盒化**：用户全程无需打开 ComfyUI 界面。
