# Changelog

本项目的版本说明遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 的结构。

## [Unreleased]

### Added

- 新增 Direct mode：单模块、低风险、单一语义产物可直接路由、执行和交付，不创建完整工作流或 STOP。
- 新增 `autoflow.py direct-route` 与 `autoflow.py review`，分别用于轻量本地能力路由和四类 STOP 审核信息包。

### Changed

- `submit/` 只接受可直接交付的最终内容：`package_submission.py` 新增硬拒绝——编译产物（`dist`/`build`/`target`/`out`/`bin`/`obj`/`.next`/`.gradle`/`.idea`/`.vscode`/`coverage` 等目录与 `*.exe`/`*.dll`/`*.so`/`*.class` 等后缀）与 AutoFlow 运行元数据（`manifest.json`、`*_manifest.json`、`workflow.json`、`artifact_manifest.json`、`run_state.json` 等）；`--verify-only` 的 `no_sensitive_files` 检查扩展到已发布文件夹（原先只查 zip），并在结果中输出 `forbidden` 明细。
- 打包 manifest（`autoflow/package-manifest/1.0`）从 `submit/` 移到 `.autoflow/intermediate/plans/`（运行受管区，不再混入交付内容）；`validate_package_acceptance` 相应豁免 `package.manifest` 的 submit 位置约束，bundle/zip/folder 仍必须在 `submit/` 下。
- 图片验收为纯人工决策：删除 `check_images.py`（AI 视觉预检），任何路由、任何内容生成的图片都不做 AI/自动预检，生成后直接进入人工 `VISUAL_STOP` 审核；`modules/image.md` 同步移除 pre-check 指引。
- `init` 的 `--output-dir` 改为可选：缺省时 run 锚定到 request 文件所在目录（任务项目根），不再落在会话工作区根目录；显式传参仍可覆盖。SKILL.md 与 `references/directory-layout.md` 同步更新。
- 文档操作统一为 `office` 模块：`modules/office.md` 统一入口，按 `format` 分发 word/ppt/excel 子模块；产物统一为 `office.document` + `office.validation`，验证器统一为 `office_acceptance`。
- Word/PPT 处理后端从内嵌 .NET/pptxgenjs 集成重构为 `officecli` 二进制驱动（`scripts/office_engine.py` + `scripts/validate_office.py`），支持 docx/pptx/xlsx 三格式，能力检测为 `detect_office_backend`。
- 移除 `integrations/minimax-docx` 与 `integrations/presentation-skill`，集成目录只保留仍在使用的集成。
- 移除 `integrations/superpowers`、`integrations/webapp-testing`、`integrations/agent-skills`、`integrations/engineering-quality` 四个方法论/浏览器集成：路由不再注入外部方法论 Skill（`skill_names`/`global_skill_names` 清空，仅保留本地的 `impeccable` 绑定），`validate_capabilities` 删除对应硬门禁，`image.capture` 路由内联为本地 Playwright 检测（`capture_frontend_screenshots.py`），删除 `scripts/engineering_quality_adapter.py` 与 `env_setup.py`/`env_check.ps1` 中的对应路径项；集成目录仅剩 `nature-figure` 与 `impeccable`。
- 多 office 步骤（如 word + ppt 双分支 recipe）允许共享 `office.document`/`office.validation` 产物声明，manifest 按 producer 区分登记。
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
