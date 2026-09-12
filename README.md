<div align="center">

# AutoFlow.skill

面向可验证交付的 Agent Skill：小任务可直接执行，关联任务以可续跑 DAG 管理。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/qiuy-collab/AutoFlow.skill/actions/workflows/ci.yml/badge.svg)](https://github.com/qiuy-collab/AutoFlow.skill/actions)

**简体中文 · [English](README.en.md)**

</div>

AutoFlow 提供 direct 与 managed 两种模式，覆盖 task、image、office、video 和 package。managed 模式在 PLAN、SOURCE、VISUAL、DELIVERY 四类 STOP 门停下等待用户决策，计划、状态、审批和产物哈希均落盘，可检查也可续跑。

## Quick Start

复制下面整段发给你的 Agent，它会自动从 GitHub 安装并初始化：

```text
请从 https://github.com/qiuy-collab/AutoFlow.skill 获取并安装 AutoFlow Skill。

1. 克隆仓库或下载其完整内容；根据你正在运行的客户端约定，确定该客户端的 Skill 安装目录（例如 ~/.newmax/skills/、~/.claude/skills/ 或该客户端文档规定的位置），将完整 autoflow Skill 目录安装进去。不要假设或硬编码 Codex 专属路径。
2. 确认安装后的目录包含 SKILL.md、references/、modules/、scripts/、integrations/、requirements.txt，且所有相对引用仍从 Skill 根目录可达。
3. 在 Skill 根目录先阅读 references/init.md。检查 Python、pip、Git、Node；安装 requirements.txt 的 Python 依赖。按需安装 Playwright 与 chromium、Mermaid CLI、D2、officecli、.NET 和 ffmpeg；复杂 Word 报告/论文默认使用 integrations/minimax-docx，Agent 也可按任务选择 officecli。
4. 在 Skill 根目录运行：python scripts/autoflow.py env-check --json 和 python scripts/autoflow.py capabilities --json。逐项汇报 available、missing 或 incomplete，不得输出 APIKEY。
5. 不要替用户创建、猜测或写入 .env 中的 BASEURL、APIKEY、VALIDATOR_* 等凭据。凭据缺失时，说明 AI 生图和提示词质检被阻塞，并等待用户自行配置后再继续。
```

安装完成后，任务规模决定执行模式：单模块、无依赖的小交付走 direct；涉及来源选择、相互依赖、文档、打包或可恢复状态的交付走 managed。

## 效果总览

以下全部由同一个演示项目「基于 Spring Boot + MySQL 的校园活动报名管理系统」生成。

| 填写前 | 填写后 |
| --- | --- |
| <img src="display/word/render/before-01.png" alt="填写前的实验报告模板" width="360"> | <img src="display/word/render/filled-en-1.png" alt="填写后的实验报告页面" width="360"> |

## Image 模块

Image 模块覆盖四种子类，以下展示全部能力。

### capture 真实浏览器截图

通过 Playwright 对本地运行的 Web 应用进行真实捕获。

```bash
python scripts/capture_frontend_screenshots.py --config <capture-plan.json> --output-dir <dir>
```

| | | |
|:---:|:---:|:---:|
| ![dashboard](display/images/capture/01-dashboard.png) | ![calendar](display/images/capture/02-activity-calendar.png) | ![registration](display/images/capture/03-registration.png) |
| dashboard | activity-calendar | registration |
| ![operations](display/images/capture/04-operations.png) | | |
| operations | | |

### ai AI 生成截图

覆盖终端命令、IDE 开发、Linux 运维和 nature-figure 科研图形摘要四类场景。

```bash
python scripts/generate_images.py --config <prompt-config.json>
```

| | | |
|:---:|:---:|:---:|
| ![maven-terminal](display/images/ai/01-java-maven-terminal.png) | ![vscode](display/images/ai/02-registration-controller-vscode.png) | ![graphical-abstract](display/images/ai/03-campuspulse-graphical-abstract.png) |
| Maven 构建 | VS Code 源码 | 图形摘要 |
| ![sql-query](display/images/ai/04-linux-sql-query.png) | ![network-ss](display/images/ai/05-linux-network-ss.png) | ![git-commit](display/images/ai/06-git-commit-terminal.png) |
| SQL 查询 | 网络验证 | Git 提交 |
| ![debug-breakpoint](display/images/ai/07-vscode-debug-breakpoint.png) | ![devtools](display/images/ai/08-browser-devtools-network.png) | ![maven-test](display/images/ai/09-terminal-maven-test.png) |
| VS Code 调试 | DevTools 网络面板 | Maven 测试 |

### diagram 确定性图表

基于 DSL 渲染，输出架构图、ER 图、流程图、类图、时序图、用例图和网络拓扑图。

```bash
python scripts/generate_diagram_assets.py --config <diagram-plan.json> --output-dir <dir>
```

| | | |
|:---:|:---:|:---:|
| ![architecture](display/images/diagram/campus-activity-architecture.png) | ![er](display/images/diagram/campus-activity-er.png) | ![flow](display/images/diagram/campus-registration-flow.png) |
| 系统架构 | ER 关系 | 业务流程 |
| ![class](display/images/diagram/campus-activity-class.png) | ![sequence](display/images/diagram/campus-registration-sequence.png) | ![usecase](display/images/diagram/campus-system-usecase.png) |
| 类图 | 时序图 | 用例图 |
| ![topology](display/images/diagram/campus-network-topology.png) | | |
| 部署拓扑 | | |

### chart 数据图表

基于 nature-figure 出版级图表模板，支持火山图、ROC 曲线、点图、边缘分布图等。

```bash
python integrations/nature-figure/scripts/plot_templates.py <template> ...
```

| | | |
|:---:|:---:|:---:|
| ![metric-matrix](display/images/chart/activity-metric-matrix.png) | ![capacity](display/images/chart/capacity-vs-registration.png) | ![volcano](display/images/chart/activity-volcano.png) |
| 指标矩阵 | 容量对比 | 火山图 |
| ![roc](display/images/chart/checkin-model-roc.png) | ![dotplot](display/images/chart/activity-category-dotplot.png) | ![marginal](display/images/chart/registration-marginal.png) |
| ROC 曲线 | 类别点图 | 边缘分布 |

## Office 模块

### Word 模板填写

Reading the report template, filling each section with real project evidence, validating via officecli, and rendering page by page.

```bash
python scripts/office_engine.py --action fill --format word ...
python scripts/validate_office.py <file>.docx
```

| Page 1 | Page 2 |
|:---:|:---:|
| ![filled-en-1](display/word/render/filled-en-1.png) | ![filled-en-2](display/word/render/filled-en-2.png) |
| Page 3 | |
| ![filled-en-3](display/word/render/filled-en-3.png) | |

### Word 从零创建

Creating a graduation thesis from scratch with abstract, chapters, and results, validated page by page via officecli.

| Page 1 | Page 2 |
|:---:|:---:|
| ![thesis-en-1](display/document-from-scratch/render/thesis-en-1.png) | ![thesis-en-2](display/document-from-scratch/render/thesis-en-2.png) |
| Page 3 | Page 4 |
| ![thesis-en-3](display/document-from-scratch/render/thesis-en-3.png) | ![thesis-en-4](display/document-from-scratch/render/thesis-en-4.png) |

### Excel 创建

通过 officecli 创建带样式和公式的电子表格。

```bash
python scripts/office_engine.py --action create --format excel ...
```

![Excel 报名统计表](display/excel/render/sheet-1.png)

## 链路总览

```mermaid
flowchart LR
    R[用户请求] --> Q{单模块、低风险、无依赖?}
    Q -->|是| D[direct: 初始化工作区与 submit/]
    D --> DA[执行并校验最小交付]
    Q -->|否| M[managed: 初始化 DAG]
    M --> P[PLAN STOP]
    P --> T[task / GitHub 来源]
    T --> S[SOURCE STOP]
    S --> I[image / office / video]
    I --> V[VISUAL STOP]
    V --> K[package 与验收]
    K --> L[DELIVERY STOP]
```

## 五个模块速查

| 模块 | 用途 |
| --- | --- |
| `task` | GitHub-first 检索、项目构建、计算和可运行性证据。 |
| `image` | 真实捕获、AI 生成电脑截图、确定性图和基于真实数据的图表。 |
| `office` | Word、PPT、Excel 的创建、填充、渲染审查和计划级校验。 |
| `video` | 既有视频分析、录制、生成和处理。 |
| `package` | 依据需求组装干净的 `submit/` 交付目录与可验证清单。 |

## 插件

AutoFlow 默认内置以下四个插件，用户可自行添加更多：

| 插件 | 用途 |
| --- | --- |
| `officecli` | Office 文档的结构化编辑、OpenXML 校验和 HTML 渲染。 |
| `minimax-docx` | 复杂 Word 报告/论文创建与填充后端；由 Agent 按任务选择，仍由 `officecli` 校验和渲染。 |
| `impeccable` | 前端设计语言与离线质量检测适配。 |
| `nature-figure` | 具有数据来源和质量记录的出版级图表模板。 |

## 赞助商

[sshzyu.com](https://sshzyu.com) 提供 AI 生图功能 API。

## 常见问题

- `capabilities` 显示缺失：先按 [环境初始化](references/init.md) 安装对应依赖，再重新检查。
- AI 路由被阻塞：仅由用户配置 `.env` 的 `BASEURL`、`APIKEY` 和可选 `VALIDATOR_*`；不要伪造图片。
- 浏览器截图失败：确认本地应用可访问，安装 `playwright` 后执行 `python -m playwright install chromium`。
- Mermaid 或 D2 不可用：安装对应 CLI，并用 `autoflow.py capabilities --json` 确认渲染器已被识别。
- Office 校验失败：用 `officecli validate` 和 `officecli view <file> issues --json` 定位问题，再运行 `office_engine.py` 与 `validate_office.py`。
- 工作流拒绝完成节点：检查每个声明产物的绝对路径和哈希；修改已登记产物时先运行 `autoflow.py revise`。
- `submit/` 被拒绝：移除构建输出、缓存、编辑器元数据、密钥和 AutoFlow 运行元数据，只保留最终交付物。

## 测试

```bash
python -m unittest discover -s tests
```

## License

[MIT](LICENSE) © [qiuy-collab](https://github.com/qiuy-collab)
