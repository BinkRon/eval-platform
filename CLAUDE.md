# 对话 Agent 评测平台

## 项目概述

独立的对话 Agent 评测产品，解决"Agent 做得好不好"的问题。核心理念：**对练机器人模拟用户 + 裁判机器人自动评判**。任何对话机器人只要暴露对话 API 就能接入评测。

技术栈：Python + FastAPI + PostgreSQL + SQLAlchemy 2.0 + React + TypeScript + Vite + Ant Design + TanStack Query

## 当前状态

版本：v0.1 MVP
进度：Phase A 未开始
详见：`docs/progress.md`

## 文档索引

| 级别 | 文档 | 说明 |
|------|------|------|
| 每次必读 | `docs/progress.md` | 开发进度、交接备注 |
| 开发参考 | `docs/architecture.md` | 技术架构、数据库、API、核心引擎 |
| 开发参考 | `docs/conventions.md` | 代码规范、命名、Git 规范 |
| 开发参考 | `docs/testing.md` | 测试策略、编写规范 |
| 按需查阅 | `docs/eval-platform-mvp-spec.md` | MVP 产品需求细节（页面布局、交互、字段规则） |
| 归档 | `docs/archive/eval-platform-framework.md` | 产品完整愿景（含未纳入 MVP 的功能） |
| 归档 | `docs/archive/project-roadmap.md` | 跨项目总规划（含编排平台） |

## Session 工作流程

### 开始时（必做）
1. 读取本文件 → 了解项目概况和当前状态
2. 读取 `docs/progress.md` → 了解进度和上次交接点
3. 按需读取 `docs/architecture.md` 或 `docs/conventions.md`
4. 判断当前任务性质，选择工作模式：
   - **progress.md 有"进行中"的任务** → 直接执行
   - **需要规划新阶段** → 使用 EnterPlanMode，确认方向后再动手

### 开发中
- 写完一个任务的代码后，用 **code-reviewer** 和 **architecture-guard** 并行审查
- 审查通过后，调用 `/commit` 提交
- 每完成一个任务，立即更新 `docs/progress.md`

### 结束前（必做）
1. 更新 `docs/progress.md` — 标记完成项、更新进行中项、写交接备注
2. 更新本文件的"当前状态"
3. 如有新的架构决策 → 更新 `docs/architecture.md`
4. 如有新的代码约定 → 更新 `docs/conventions.md`

## 开发规则

- 后端所有接口返回统一的 JSON 格式，错误时包含 `detail` 字段
- 前端错误提示统一用 Ant Design `message` 组件
- 数据库操作使用 SQLAlchemy ORM，不手写 SQL
- 删除操作处理关联实体（级联删除或置空外键）
- LLM 调用通过适配层统一接口，不直接调用厂商 SDK
- 详细的数据模型、API 设计、核心引擎设计见 `docs/architecture.md`
- 详细的代码规范见 `docs/conventions.md`
