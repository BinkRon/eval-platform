# 对话 Agent 评测平台

## 项目概述

独立的对话 Agent 评测产品，解决"Agent 做得好不好"的问题。核心理念：**对练机器人模拟用户 + 裁判机器人自动评判**。任何对话机器人只要暴露对话 API 就能接入评测。

技术栈：Python + FastAPI + PostgreSQL + SQLAlchemy 2.0 + React + TypeScript + Vite + Ant Design + TanStack Query

## 当前状态

版本：v0.2 架构重构（已完成）
基线：v0.1 MVP 已完成（Phase A-F）
当前：Phase 1-5 + 端到端验收 全部完成
详见：`docs/progress.md`

## 文档索引

| 级别 | 文档 | 说明 |
|------|------|------|
| 每次必读 | `docs/progress.md` | 开发进度、交接备注 |
| 开发参考 | `docs/architecture.md` | 技术架构、数据库、API、核心引擎 |
| 开发参考 | `docs/conventions.md` | 代码规范、命名、Git 规范 |
| 开发参考 | `docs/testing.md` | 测试策略、编写规范 |
| 开发参考 | `docs/eval-platform-mvp-spec-v2.md` | v2 产品需求（页面下钻架构、对话剧场） |
| 归档 | `docs/eval-platform-mvp-spec.md` | v1 MVP 产品需求（已被 v2 取代） |
| 归档 | `docs/archive/eval-platform-framework.md` | 产品完整愿景（含未纳入 MVP 的功能） |
| 归档 | `docs/archive/project-roadmap.md` | 跨项目总规划（含编排平台） |

## Session 工作流程

### 开始时（必做）
1. 读取本文件 → 了解项目概况和当前状态
2. 读取 `docs/progress.md` → 了解进度和上次交接点
3. 按需读取 `docs/architecture.md` 或 `docs/conventions.md`
4. 判断当前任务性质，选择工作模式：
   - **progress.md 有”进行中”或”待开始”的步骤或阶段** → 可以不需要进入 plan 模式，自己先思考一下该如何 plan 然后直接执行即可
   - **需要规划新版本的整体步骤/阶段**（用户明确提出，或所有步骤已完成） → 使用 EnterPlanMode，等用户确认方向后再动手

### 开发中（每个任务的标准流程）
1. **编码**：按 `progress.md` 中的任务描述实现
2. **自动测试**：后端改动必须跑 `pytest`；前端改动确保 `tsc --noEmit` 无报错
3. **代码审查**：用 **code-reviewer** 和 **architecture-guard** 并行审查
4. **修复**：根据审查结果修复问题
5. **提交**：审查通过后，调用 `/commit` 提交
6. **更新进度**：立即在 `docs/progress.md` 中勾选已完成任务

### Session 粒度
- 一个 session 执行一个完整的 Phase（非单个小任务），执行完后让用户确认是否继续
- Phase 内的任务按顺序执行，每个任务走完上述标准流程
- 如果 Phase 过大无法在一个 session 完成，在交接备注中标明断点

### 结束前（必做）
1. 更新 `docs/progress.md` — 标记完成项、更新进行中项、写交接备注
2. 更新本文件的”当前状态”（版本号、当前 Phase）
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
