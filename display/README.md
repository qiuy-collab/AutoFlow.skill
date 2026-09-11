# AutoFlow 演示产物

本目录以同一个可运行项目「基于 Spring Boot + MySQL 的校园活动报名管理系统」展示 AutoFlow 的四类视觉链路和两类 Word 链路。展示目录只保留最终 PNG 与可交付 DOCX；配置、DSL、提示词、生成报告和运行日志均保存在任务的 `.autoflow/intermediate/`。

| 目录 | 链路与产出命令 | 看点 |
| --- | --- | --- |
| `images/capture/` | `scripts/capture_frontend_screenshots.py --config <capture-plan.json> --output-dir <dir>` | 本地运行的 CampusPulse 页面。活动日历和运营看板使用 selector 范围完整截图，未因超出视口而截断。 |
| `images/ai/` | `scripts/validate_prompt.py` 后执行 `scripts/generate_images.py --config <prompt-config.json>`；图形摘要使用 `scripts/generate_scientific_schematic.py` | 与当前 Java 项目对应的 AI 生成终端、VS Code 与非定量图形摘要。它们是文档视觉素材，不替代真实运行证据。 |
| `images/diagram/` | `scripts/generate_diagram_assets.py --config <diagram-plan.json> --output-dir <dir>` | 系统架构、核心 ER 关系和报名业务流程的确定性渲染。 |
| `images/chart/` | `integrations/nature-figure/scripts/plot_templates.py <template> ...` | 基于 MySQL seed 数据的报名、容量与签到指标图，不使用模拟值。 |
| `word/` | `officecli view <file>.docx html --browser` 后逐页渲染 | `template.docx` 是填写前模板，`filled.docx` 是使用真实项目证据填写后的实验报告；`render/` 保留逐页 PNG。 |
| `document-from-scratch/` | `officecli` 创建、校验和 HTML 渲染 | 从零创建的毕业设计论文及四页渲染复查图，内容与同一项目的数据模型、页面和测试结论一致。 |

真实环境证据包括 Maven 测试通过、Spring Boot 健康和业务端点返回 HTTP 200，以及本地 MySQL 中 4 个活动、8 名学生、12 条报名和 11 条签到记录。志愿服务活动为 3/4 签到，到场率 75%。
