<div align="center">

# AutoFlow.skill

**让 Agent 把多个步骤、多个 Skills 和多个交付物组织成一条可验证的工作流。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-3.1-blue.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

</div>

---

## AutoFlow 是什么

AutoFlow 不再是一条固定的实验报告流水线。它把复杂任务拆成六类模块，再按需求组合成有依赖关系的工作流：

- `task`：调研、GitHub 源码选型、项目改造、计算和真实执行
- `image`：真实截图、AI 资产、图示和数据图表
- `word`：Word 创建、编辑和模板填写
- `ppt`：通过本地审计的 `presentation-skill` 集成创建或编辑演示文稿
- `video`：分析、录屏、创建和处理视频
- `package`：按需求整理交付目录和压缩包

Agent 负责理解任务和调用工具，Python 核心负责检查 DAG、步骤状态、STOP 和真实产物。这样既能灵活组合 Skills，也不会把关键选择藏在一段长对话里。

AutoFlow 3.1 重新纳入 AutoLab 已验证的课程交付约束：需求/评分项必须映射到证据，Word 模板填写必须生成结构验收报告，视频必须记录媒体探测结果，打包文件必须映射需求并通过敏感文件扫描，最终交付必须逐项填写机器可检查的审查记录。

## 典型组合

| Recipe | 工作流 |
|---|---|
| `lab-report` | task → image → word → package |
| `report-and-slides` | task → image → word + ppt → package |
| `project-delivery` | GitHub discovery → build → image → package |
| `project-and-report` | GitHub discovery → build → image → word → package |
| `project-report-and-slides` | GitHub discovery → build → image → word + ppt → package |
| `video-delivery` | video → package |
| `document` | 可选 task/image → word |
| `presentation` | 可选 task/image → ppt |
| `custom` | Agent 根据需求生成任意 DAG |

## 四类 STOP

- `PLAN_STOP`：先展示完整工作流和交付范围，用户确认后执行。
- `SOURCE_STOP`：GitHub 有合适候选时列出 3–5 个，让用户选定后再克隆和改造。
- `VISUAL_STOP`：新图片、图表或 PPT 生成后先展示，批准后才进入下游。
- `DELIVERY_STOP`：全部校验通过后展示交付清单，用户签收后完成。

没有合适 GitHub 项目时，AutoFlow 会记录查询和排除理由，然后从头实现，不制造凑数候选。

## Quick Start

把下面这段发给 Agent：

```text
请使用 autoflow 完成这个任务。

先读取 SKILL.md，根据需求选择 recipe 或使用 `recipe auto` 生成可解释的 recipe 推荐。
生成 WORK_PLAN.md 后停下来让我确认；不要绕过源码、视觉和交付 STOP。
```

手动初始化一个运行目录：

```bash
python scripts/autoflow.py init \
  --request-file request.md \
  --output-dir autoflow \
  --recipe lab-report

python scripts/autoflow.py status --workflow autoflow/.autoflow/config/workflow.json
python scripts/autoflow.py validate --workflow autoflow/.autoflow/config/workflow.json
```

AutoFlow 没有“一键执行全部”的 `run` 命令。Agent 根据 ready steps 调用对应模块，核心 CLI 只验证和推进状态：

```bash
python scripts/autoflow.py next --workflow autoflow/.autoflow/config/workflow.json
python scripts/autoflow.py integrations --json
python scripts/autoflow.py route --workflow autoflow/.autoflow/config/workflow.json --step build --json
python scripts/engineering_quality_adapter.py route --module task --action build --json
node scripts/impeccable_adapter.mjs detect --json src/
python scripts/autoflow.py transition --workflow autoflow/.autoflow/config/workflow.json --step task --to running
python scripts/autoflow.py transition --workflow autoflow/.autoflow/config/workflow.json --step task --to completed --artifact task.result=C:/absolute/result.json
```

## 运行目录

```text
autoflow/
├── .autoflow/
│   ├── scripts/              # 本次任务专用脚本
│   ├── runtime/              # 自动补齐的隔离运行环境，不进入交付包
│   ├── intermediate/         # 中间产物、验证报告、日志和计划
│   │   ├── plans/            # GitHub、图片、Word、PPT、视频、打包计划
│   │   ├── artifacts/        # 截图、图表、Word/PPT 验收报告等
│   │   └── verification/     # 源码隔离复测区，禁止在 submit 中运行
│   └── config/               # workflow、状态、需求映射、审批和请求副本
└── submit/                   # 最终源码、论文、PPT、视频和 ZIP
```

旧版 AutoLab `workflow.json` 不兼容，需要重新初始化。

## 环境检查

```bash
python scripts/env_setup.py --check-only --route all --no-probe
```

按模块准备环境：

```bash
python scripts/env_setup.py --route capture
python scripts/env_setup.py --route diagram
python scripts/env_setup.py --route video
python scripts/env_setup.py --route ai
```

AI 图片需要 `.env` 中的 `BASEURL` 和 `APIKEY`。Word 模块使用仓库内 `integrations/minimax-docx` 的集成内核，浏览器证据使用仓库内 `integrations/webapp-testing`，PPT 模块使用仓库内 `integrations/presentation-skill` 的 renderer 与 QA；缺少 Node/Python 依赖时会在 PLAN 阶段阻断，不调用用户级或插件 Skill。

Word 生成完成后必须运行内置验证器：

```bash
python scripts/validate_word.py \
  --document autoflow/.autoflow/intermediate/artifacts/report.docx \
  --template template.docx \
  --plan autoflow/.autoflow/intermediate/plans/word.json \
  --report autoflow/.autoflow/intermediate/artifacts/word_validation.json
```

Word 步骤只有同时提交 `word.document` 和通过的 `word.validation` 才能完成。

## 项目结构

```text
autoflow/
├── SKILL.md                  # 精简路由入口
├── modules/                  # 六个能力模块
├── references/               # Workflow 与 STOP 协议
├── recipes/                  # 内置 DAG 模板
├── examples/                 # Schema、计划和交付示例
├── scripts/
│   ├── autoflow.py           # 状态与校验 CLI
│   ├── autoflow_core.py      # DAG、Gate、artifact 核心
│   ├── validate_word.py      # DOCX 模板、TOC、题注、口吻和结构验收
│   ├── generate_images.py
│   ├── capture_frontend_screenshots.py
│   ├── generate_diagram_assets.py
│   ├── video_process.py
│   ├── engineering_quality_adapter.py
│   ├── impeccable_adapter.mjs
│   └── package_submission.py
├── tests/                    # 标准库单元与集成测试
├── evals/                    # Skill 场景评测
├── docs/                     # 规则和 GitHub Pages
└── integrations/             # 已审计、可复现的集成内核与外部 Skill 来源记录
    ├── minimax-docx/         # 集成的 DOCX/OpenXML 内核、规则和 XSD
    ├── nature-figure/        # nature-figure 来源、许可证和适配说明
    ├── webapp-testing/       # 集成的 Playwright 网页测试与浏览器证据 Skill
    ├── superpowers/          # 集成的规划、TDD、调试、审查和验证方法 Skill
    ├── impeccable/           # 集成的前端设计规则、命令和离线质量检测器
    ├── engineering-quality/  # 集成的代码审查、安全、性能和发布质量 Skill
    ├── agent-skills/         # 集成的规划、接口、前端、调试、观测和交付增强 Skill
    └── presentation-skill/   # 集成的 PPTX renderer、模板和几何/视觉 QA
```

各目录职责和外部能力集成策略见 `references/directory-layout.md`。

运行时数据不属于 Skill 包：每个任务的持久化工作流放在用户工作区的 `autoflow/.autoflow/`，最终交付放在 `autoflow/submit/`；Skill 根目录下的测试和后端缓存目录只在运行时临时创建，发布时不应保留。

## 当前效果示例

原 AutoLab 的报告能力现在是 `lab-report` recipe，用来验证 task/image/word/package 组合仍能完成真实交付。

### 生成的文档

![生成的文档截图](docs/效果图/生成的文档截图.png)

### 交付文件

![交付文件](docs/效果图/交付文件.png)

## 测试

```bash
python -m unittest discover -s tests -v
python -m py_compile scripts/*.py tests/*.py
```

The CLI regression suite includes a real “student management system + paper +
defense slides” planning smoke. It verifies the compound recipe, keeps
`PLAN_STOP` pending, routes every step to local Skill files, and does not fake
SOURCE_STOP or user approval.

测试覆盖 DAG 循环、状态转换、四类 STOP、GitHub 有/无候选、需求证据映射、Word 强验收、视频/包报告、敏感文件拒绝、视觉阻断、产物哈希、旧格式拒绝和 CLI 初始化。

## License

MIT License © [qiuy-collab](https://github.com/qiuy-collab)

项目地址：[qiuy-collab/AutoFlow.skill](https://github.com/qiuy-collab/AutoFlow.skill)
