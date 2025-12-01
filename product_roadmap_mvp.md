# 🚀 ComfyUI-Flow MVP 产品开发进度追踪

**版本**: 1.1 | **阶段**: Private Beta (里程碑 1.5)  
**目标**: 验证核心价值，跑通“角色导演”全流程。
**战略方向**: Serverless First (以低运维成本为最高优先级)

---

## 📊 总体进度概览

| 模块 | 进度状态 | 负责人 | 备注 |
| :--- | :--- | :--- | :--- |
| **P0: 核心后端** | 🟢 **85%** | CTO (Cursor) | 核心逻辑已跑通。**架构已转型为 Serverless 预备态**。 |
| **P1: 用户界面** | 🟢 **90%** | CEO & CTO | 驾驶舱 UI 已完成，交互丝滑。需做 UI 减法。 |
| **P2: 营销获取** | 🔴 **0%** | CEO | 尚未开始。需要 Landing Page。 |

---

## ✅ P0: 核心后端 & API (The Core Engine)

| 功能点 | 详细描述 | 状态 | 预计完成 | 技术备注 |
| :--- | :--- | :--- | :--- | :--- |
| **1. ComfyDeploy 代理** | 封装 ComfyUI 调用，处理云端/本地双驱逻辑。 | ✅ **已完成** | - | 当前本地 FastAPI 作为 **Serverless 模拟器** 运行。 |
| **2. API Key 认证** | 拦截请求，验证 Key 有效性，拒绝未授权访问。 | ✅ **已完成** | - | 基于 `AuthManager`，未来无缝迁移至 Vercel Middleware。 |
| **3. 基础用量限制** | 防止单个 Key 滥用 (Rate Limiting / Quota)。 | 🟡 **待开发** | TBD | 需在 `generate` 接口前增加计数检查逻辑。 |
| **4. Serverless 迁移** | 将本地 Python 逻辑迁移至 Vercel Edge Functions。 | 🔵 **规划中** | Launch前 | 移除对本地 SQLite 的依赖，改为无状态/KV存储。 |

---

## ✅ P1: 核心前端 & 用户界面 (The Cockpit)

| 功能点 | 详细描述 | 状态 | 预计完成 | 技术备注 |
| :--- | :--- | :--- | :--- | :--- |
| **5. "驾驶舱" UI** | 图片上传、Prompt 输入、生成按钮、结果展示。 | ✅ **已完成** | - | `batch_generation_dashboard.html` 已包含所有核心组件。 |
| **6. 前后端交互** | Loading 动画、错误反馈、结果渲染、认证拦截。 | ✅ **已完成** | - | 已修复登录闪烁和刷新问题，体验丝滑。 |
| **7. UI 简化 (Optimization)** | **新增任务**: 隐藏 seed/cfg/steps 等技术参数，聚焦 Prompt。 | 🟡 **待优化** | TBD | 需修改 HTML/CSS，默认折叠或移除高级选项。 |

---

## 🚧 P2: 营销与用户获取 (The Front Door)

| 功能点 | 详细描述 | 状态 | 预计完成 | 技术备注 |
| :--- | :--- | :--- | :--- | :--- |
| **8. 营销着陆页** | 纯静态页 `index.html`。展示价值主张，引导申请。 | 🔴 **未开始** | TBD | 需新建文件，设计高转化率的文案和配图。 |
| **9. 邮箱收集表单** | 内嵌 Tally/Typeform 表单，收集种子用户邮箱。 | 🔴 **未开始** | TBD | 第三方工具嵌入，零代码开发。 |

---

## 🏗️ 技术架构决策记录 (ADR)

### 1. 后端架构：FastAPI vs Vercel Serverless
*   **决策**: **战略转向 Vercel Serverless + ComfyDeploy**。
*   **原定方案**: FastAPI (VPS/Docker) - *已废弃*。
*   **新理由 (CEO 决策)**:
    *   **零运维**: 彻底消除服务器维护成本（安全补丁、宕机、磁盘管理），释放 CEO 精力聚焦产品。
    *   **解决超时**: 利用 **ComfyDeploy** 作为专用的 Serverless GPU 后端，解决 Vercel 的 10s/60s 超时限制。
    *   **低成本**: MVP 阶段按量付费，无闲置服务器成本。
    *   **当前状态**: **Local Dev Simulator**。本地开发环境继续使用 FastAPI 模拟 Serverless 行为，保持开发速度，上线前进行轻量级迁移。

### 2. 认证方案：Manual Keys vs OAuth
*   **决策**: 使用 **预制 API Key (Manual)**。
*   **理由**:
    *   MVP 阶段用户少，手动发号（微信/邮件）最具仪式感，且开发成本最低。
    *   无需对接 Google/GitHub 登录，避免复杂的 OAuth 流程和回调处理。

---

## 📝 每日待办 (Daily TODOs)

- [ ] **UI 减法 (P1-7)**：隐藏非核心参数，让界面更像“导演工具”而非“调试器”。
- [ ] **实现 P0-3 用量限制**：简单计数器，为按量付费做准备。
- [ ] **创建 Landing Page**：搭建 `index.html` 框架。

---

**Last Updated**: 2025-12-01
