<div align="center">

# AutoFlow.skill

面向多步骤交付任务的可验证 Agent Skill。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/qiuy-collab/AutoFlow.skill/actions/workflows/ci.yml/badge.svg)](https://github.com/qiuy-collab/AutoFlow.skill/actions)

**简体中文 · [English](README.en.md)**

</div>

## 它是什么

AutoFlow 给兼容的 Agent 客户端加一层工作流:调研、代码、截图、文档、PPT、视频、打包,变成一张带依赖、审批和产物校验的 DAG。

活是 Agent 干的。AutoFlow 负责留痕——计划、状态、审批、产物都存在文件里,不进聊天记录。所以任务随时可查,中断后能接着跑。

## 快速开始

把这句话连同任务交给 Agent:

```text
使用 autoflow 完成这个任务。先读 SKILL.md,选好 recipe,生成 WORK_PLAN.md
后等我确认;不要跳过 SOURCE、VISUAL 和 DELIVERY STOP。
```

也可以直接用 CLI:

```bash
python scripts/autoflow.py init \
  --request-file request.md \
  --output-dir autoflow \
  --recipe auto

python scripts/autoflow.py next \
  --workflow autoflow/.autoflow/config/workflow.json

python scripts/autoflow.py status \
  --workflow autoflow/.autoflow/config/workflow.json
```

## 四个 STOP 门禁

AutoFlow 在四个检查点停下。每次请求确认前,必须展示可审核的信息包——证据和路径,而不是一句"行吗":

- **PLAN** — 工作范围、步骤、预期产物
- **SOURCE** — 代码任务的 GitHub 候选项目
- **VISUAL** — 图片、图表、视觉型 PPT
- **DELIVERY** — 交付清单,用户签收

找不到合适的 GitHub 候选时,AutoFlow 保留查询记录和排除理由,从头实现。它不会为了走流程编造候选。

## 模块

`task` · `image` · `office` · `video` · `package`

自由组合成 recipe:`lab-report`、`project-delivery`、`report-and-slides`、`custom` DAG。工作流契约见 [`references/workflow-contract.md`](references/workflow-contract.md)。

## 它不是

- 不是低代码平台——那是 n8n / Coze / Dify
- 不是图框架——那是 LangGraph
- 没有"一条命令假装全部完成"的模式——每个产物交付前都要过校验

## 目录结构

```text
SKILL.md        路由入口
modules/        task / image / office / video / package（office 按 format 分发 word/ppt/excel）
recipes/        内置 DAG 模板
references/     工作流、STOP、验收、环境契约
integrations/   已审计并固定版本的内置能力
scripts/        状态机、适配器、各模块后端
tests/          单元与集成测试
examples/       真实交付样例
docs/           GitHub Pages
```

## 测试

```bash
python -m unittest discover -s tests
```

## License

[MIT](LICENSE) © [qiuy-collab](https://github.com/qiuy-collab)
