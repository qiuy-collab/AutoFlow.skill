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
- `ppt`：通过已安装的 `pptx` Skill 创建或编辑演示文稿
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

先读取 SKILL.md，根据需求选择 recipe 或生成 custom DAG。
生成 WORK_PLAN.md 后停下来让我确认；不要绕过源码、视觉和交付 STOP。
```

手动初始化一个运行目录：

```bash
python scripts/autoflow.py init \
  --request-file request.md \
  --output-dir task_runs/my-run \
  --recipe lab-report

python scripts/autoflow.py status --workflow task_runs/my-run/workflow.json
python scripts/autoflow.py validate --workflow task_runs/my-run/workflow.json
```

AutoFlow 没有“一键执行全部”的 `run` 命令。Agent 根据 ready steps 调用对应模块，核心 CLI 只验证和推进状态：

```bash
python scripts/autoflow.py next --workflow task_runs/my-run/workflow.json
python scripts/autoflow.py transition --workflow task_runs/my-run/workflow.json --step task --to running
python scripts/autoflow.py transition --workflow task_runs/my-run/workflow.json --step task --to completed --artifact task.result=C:/absolute/result.json
```

## 运行目录

```text
task_runs/my-run/
├── workflow.json            # AutoFlow Schema 1.0 DAG
├── run_state.json           # 步骤和 STOP 状态
├── artifact_manifest.json   # 路径、生产者、消费者和 SHA-256
├── requirement_map.json     # 需求/评分项、验收条件、证据和计划图表
├── delivery_review.json     # 每项需求和每个产物的最终正确性审查
├── WORK_PLAN.md             # 用户确认的工作计划
└── plans/                   # GitHub、图片、Word、PPT、视频、打包等模块计划
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

AI 图片需要 `.env` 中的 `BASEURL` 和 `APIKEY`。Word 模块检测已安装的 `minimax-docx`/`documents` Skill，PPT 模块检测 `pptx`/`presentations` Skill；AutoFlow 不复制其专有实现。

Word 生成完成后必须运行内置验证器：

```bash
python scripts/validate_word.py \
  --document task_runs/my-run/artifacts/report.docx \
  --template template.docx \
  --plan task_runs/my-run/plans/word.json \
  --report task_runs/my-run/artifacts/word_validation.json
```

Word 步骤只有同时提交 `word.document` 和通过的 `word.validation` 才能完成。

## 项目结构

```text
AutoFlow.skill/
├── SKILL.md                  # 精简路由入口
├── modules/                  # 六个能力模块
├── references/               # Workflow 与 STOP 协议
├── recipes/                  # 内置 DAG 模板
├── scripts/
│   ├── autoflow.py           # 状态与校验 CLI
│   ├── autoflow_core.py      # DAG、Gate、artifact 核心
│   ├── validate_word.py      # DOCX 模板、TOC、题注、口吻和结构验收
│   ├── generate_images.py
│   ├── capture_frontend_screenshots.py
│   ├── generate_diagram_assets.py
│   ├── video_process.py
│   └── package_submission.py
├── tests/                    # 标准库单元与集成测试
├── evals/                    # Skill 场景评测
├── docs/                     # 规则和 GitHub Pages
└── vendor/                   # 可选的本地 Skill 缓存（仓库不依赖其存在）
```

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

测试覆盖 DAG 循环、状态转换、四类 STOP、GitHub 有/无候选、需求证据映射、Word 强验收、视频/包报告、敏感文件拒绝、视觉阻断、产物哈希、旧格式拒绝和 CLI 初始化。

## License

MIT License © [qiuy-collab](https://github.com/qiuy-collab)

项目地址：[qiuy-collab/AutoFlow.skill](https://github.com/qiuy-collab/AutoFlow.skill)
