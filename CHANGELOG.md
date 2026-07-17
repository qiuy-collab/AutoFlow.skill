# Changelog

本项目的版本说明遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 的结构。

## [Unreleased]

### Added

- 新增 Direct mode：单模块、低风险、单一语义产物可直接路由、执行和交付，不创建完整工作流或 STOP。
- 新增 `autoflow.py direct-route` 与 `autoflow.py review`，分别用于轻量本地能力路由和四类 STOP 审核信息包。

### Changed

- 显式调用 AutoFlow 不再强制进入 Managed mode；只有依赖、多模块、源码选型、打包、复杂证据或重要决策才使用完整 DAG。
- PLAN、SOURCE、VISUAL、DELIVERY 请求确认前必须展示对应计划、候选、实际视觉产物或交付清单及绝对路径。
- Direct mode 默认最小交付，不再为一张图附带无必要的控制文件、多个导出格式和签收流程。

## [3.1.0] - 2026-07-17

### Added

- 新增 `task`、`image`、`word`、`ppt`、`video`、`package` 六模块组合架构，以及可扩展的 recipe DAG。
- 新增 PLAN、SOURCE、VISUAL、DELIVERY 四类人工确认点，并持久化步骤、审批和产物状态。
- 代码和项目任务增加 GitHub-first 源码发现、候选评分、revision 固定和无候选 fallback。
- 内置 minimax-docx、nature-figure、presentation-skill、webapp-testing、impeccable、superpowers、agent-skills 和 engineering-quality，运行时不再依赖设备上碰巧安装的同名 Skill。
- 新增科研图、任意图示、AI 图片、网页截图、Word/PPT/视频验证与交付包检查能力。
- 增加需求到证据的映射、产物 SHA-256、隔离复测、运行耗时统计和缓存复用。

### Changed

- 项目由固定实验报告流程改为通用多产物工作流，并由 AutoLab 更名为 AutoFlow。
- 运行目录统一为 `autoflow/.autoflow/` 与 `autoflow/submit/`，中间文件不再混入交付目录。
- 环境准备改为模块级强制协议：先自动补齐，失败后尝试安装，并把结果写入可验证报告。
- Word 与 PPT 使用仓库内经过审计的本地内核；AI 图片使用 AutoFlow 自身 `.env` 中配置的上游。
- 最终源码采用“隔离复测 → 最后打包 → 只读校验”的顺序，避免复测污染 `submit/`。

### Fixed

- 修复深层 `.git` 等敏感目录可能进入交付包的问题。
- 修复已完成步骤的产物变化后无法正式重开和追踪 revision 的问题。
- 修复图片能力测试只覆盖单一 diagram 类型的问题，补齐 diagram 与 nature-figure 分类和全路线测试。
- 减少重复渲染、重复哈希和不必要的串行步骤，缩短完整工作流耗时。

### Breaking

- AutoFlow Schema 1.0 不兼容旧版 AutoLab `workflow.json`；旧任务需要重新执行 `autoflow init`。

[3.1.0]: https://github.com/qiuy-collab/AutoFlow.skill/releases/tag/v3.1.0
