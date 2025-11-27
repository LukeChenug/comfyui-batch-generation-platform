# 🚀 UI 性能优化记录：解决图片列表闪烁问题

**日期**：2025-11-26
**模块**：前端 Dashboard (`batch_generation_dashboard.html`)
**问题**：轮询更新任务状态时，已加载的图片出现周期性闪烁（重新加载）。

---

## 1. 问题现象与原因分析

### 现象
在批量生图或轮询任务状态时，页面上的任务列表会每隔几秒（轮询间隔）整体刷新一次。
表现为：
- 已完成的图片会突然变白一下再显示（闪烁）。
- 页面滚动条可能会微小跳动。
- Grid 布局下的 Masonry 排版会重新计算，导致布局抖动。

### 根本原因
原有的 `updateTaskList` 函数采用了**全量更新 (Full Re-render)** 策略：

```javascript
// 旧逻辑
taskList.innerHTML = filteredTasks.map(task => { 
    return `...HTML字符串...`; 
}).join('');
```

这意味着：
1.  每次轮询数据回来，不管数据有没有变，浏览器都会**销毁** `taskList` 下的所有 DOM 节点。
2.  然后根据新数据**重建**所有 DOM 节点。
3.  `<img>` 标签被重新创建，浏览器必须重新解析 `src`，检查 HTTP 缓存，并重新解码渲染图片。这个过程虽然快，但肉眼依然能捕捉到“白屏”瞬间。

---

## 2. 解决方案：手动 DOM 增量更新 (DOM Diffing)

为了解决这个问题，我们将渲染逻辑从“全量替换”改为“增量更新”。我们手动实现了一个轻量级的 DOM Diff 算法。

### 核心逻辑 (`updateTaskList`)

1.  **建立现有 DOM 索引**：
    首先遍历当前的 DOM 列表，建立一个 `Map<TaskId, HTMLElement>`，以便快速查找现有的任务卡片。

2.  **遍历新数据进行 Diff**：
    遍历从后端获取的最新任务列表 `filteredTasks`：
    
    *   **情况 A：新任务 (Create)**
        *   如果在 Map 中找不到该 ID，说明是新任务。
        *   `document.createElement` 创建新节点。
        *   插入到正确的位置。
    
    *   **情况 B：现有任务 (Update)**
        *   如果在 Map 中找到了，说明是旧任务。
        *   **关键判断**：读取 DOM 上的 `data-status` 和 `data-progress` 属性，与新数据对比。
        *   **只有当状态或进度发生变化时**，才更新该节点的 `innerHTML`。
        *   **如果状态没变（例如已经是 `completed`）**，则**完全不动**该节点。这样已加载的图片 DOM 结构保持原样，浏览器不需要做任何重绘工作。
    
    *   **情况 C：删除任务 (Delete)**
        *   在遍历结束后，Map 中剩余的节点说明在后端数据中已不存在（被过滤或删除了）。
        *   直接 `node.remove()` 移除。

### 代码实现摘要

```javascript
// 1. 建立索引
const existingNodesMap = new Map();
Array.from(taskList.children).forEach(node => {
    existingNodesMap.set(node.getAttribute('data-task-id'), node);
});

// 2. 增量更新循环
filteredTasks.forEach((task, index) => {
    let taskNode = existingNodesMap.get(task.task_id);
    
    if (!taskNode) {
        // A. 创建新节点
        taskNode = createNewNode(task);
        taskList.appendChild(taskNode);
    } else {
        // B. 检查更新
        const oldStatus = taskNode.getAttribute('data-status');
        const newStatus = task.status;
        
        // 只有状态变了才更新内容！这是防闪烁的关键
        if (oldStatus !== newStatus) {
            taskNode.innerHTML = renderInnerHtml(task);
            taskNode.setAttribute('data-status', newStatus);
        }
        
        // 标记为已处理
        existingNodesMap.delete(task.task_id);
    }
});

// 3. 清理旧节点
existingNodesMap.forEach(node => node.remove());
```

---

## 3. 额外优化：Grid 布局的 Loading 占位符

除了防闪烁，我们还优化了 Grid 模式下的 Loading 体验。

### 问题
Grid（瀑布流）布局依赖 JS 计算图片高度来设置 `grid-row-end`。
Loading 状态没有图片，导致高度为 0，布局塌陷。

### 解决
1.  **数据驱动高度**：在 Loading 节点的 DOM 上绑定 `data-width` 和 `data-height`（来自请求参数）。
2.  **显式占位**：
    *   CSS: `padding-bottom: ${aspectRatio}%` 撑开视觉高度。
    *   JS: `adjustLoadingGridItemHeight` 函数根据 data 属性手动计算并设置 `grid-row-end`，确保 Loading 卡片占据正确的空间。
3.  **视觉优化**：
    *   背景色：`#444444` (深灰)。
    *   样式：`border: 2px dashed #666` (去掉描边后为纯色块)。
    *   效果：Loading 块与生成的图片尺寸完全一致，生成完成后实现“无缝替换”。

---

## 4. 总结

通过这次优化，我们实现了：
1.  **零闪烁**：已完成的任务稳如泰山。
2.  **高性能**：浏览器重绘区域最小化。
3.  **丝滑体验**：Loading -> Completed 的转换平滑无缝。

保留了 `updateTaskListLegacy` 方法作为备份，以便在出问题时快速回滚。

