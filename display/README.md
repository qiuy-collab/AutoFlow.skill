# AutoFlow 演示产物

本目录以同一个可运行项目「基于 Spring Boot + MySQL 的校园活动报名管理系统」展示 AutoFlow 的四类视觉链路和四类 Office 链路。

| 目录 | 链路与产出命令 | 看点 |
| --- | --- | --- |
| `images/capture/` | `scripts/capture_frontend_screenshots.py --config <capture-plan.json> --output-dir <dir>` | 本地运行的 CampusPulse 页面。活动日历和运营看板使用 selector 范围完整截图，未因超出视口而截断。 |
| `images/ai/` | `scripts/validate_prompt.py` 后执行 `scripts/generate_images.py --config <prompt-config.json>` | 终端命令（Maven 构建、SQL 查询、网络验证、Git 提交、测试输出）、IDE 开发（VS Code 源码、调试断点）、浏览器 DevTools 和 nature-figure 科研图形摘要。它们是文档视觉素材，不替代真实运行证据。 |
| `images/diagram/` | `scripts/generate_diagram_assets.py --config <diagram-plan.json> --output-dir <dir>` | 系统架构、核心 ER 关系、报名业务流程、类图、时序图、用例图和部署拓扑的确定性渲染。 |
| `images/chart/` | `integrations/nature-figure/scripts/plot_templates.py <template> ...` | 基于 MySQL seed 数据的指标图，以及 nature-figure 出版级模板（火山图、ROC 曲线、点图、边缘分布图）。 |
| `word/` | `officecli view <file>.docx html --browser` 后逐页渲染 | `template.docx` 是填写前模板，`filled.docx` 是使用真实项目证据填写后的实验报告；`render/` 保留逐页 PNG。 |
| `document-from-scratch/` | `officecli` 创建、校验和 HTML 渲染 | 从零创建的毕业设计论文及八页渲染复查图，内容与同一项目的数据模型、页面和测试结论一致。 |
| `ppt/` | `officecli` 创建、编辑和 HTML 渲染 | 三页演示文稿（标题、架构、数据），`render/` 保留逐页 PNG。 |
| `excel/` | `officecli` 创建、编辑和 HTML 渲染 | 带公式和样式的报名统计表，`render/` 保留 PNG。 |
