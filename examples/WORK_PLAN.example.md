# AutoFlow Work Plan — 学生选课系统交付

## 目标

基于用户需求完成可运行的学生选课系统，提供真实页面证据、Word 报告和只包含规定文件的提交包。验收以核心 CRUD 可运行、证据与实现一致、文档模板完整为准。

## 需求与证据

- R1 核心 CRUD：由 `project.source`、`task.result` 和真实页面截图证明。
- R2 报告完整：由 `office.document` 和 `office.validation` 证明。
- R3 提交包准确：由 `package.bundle` 及其 manifest 证明。
- 计划图包括登录页、学生管理、课程管理和选课记录，共 4 张，均使用 `capture` 路线。

## 工作流

使用 custom DAG：`task.research → SOURCE_STOP → task.build → image.capture → VISUAL_STOP → office(word).fill → package.assemble → DELIVERY_STOP`。GitHub 候选由用户决定；系统、截图、文档和压缩包分别执行运行、视觉、结构和清单校验。

## 产物

- `project.source`：改造后的项目目录和上游归属说明。
- `task.result`：启动命令、测试命令、功能验证和 changed files 摘要。
- `image.assets`：用户批准的真实页面截图。
- `office.document`：填写后的课程设计报告。
- `office.validation`：模板结构、占位符、题注、学生口吻和渲染检查报告。
- `package.bundle`：按要求生成的提交压缩包。

## 范围与约束

只实现需求列出的学生、课程和选课 CRUD；不新增支付、云部署或无关营销页面。保留模板结构，不使用伪造运行截图，不在用户选择前克隆候选，不把缓存、密钥或整个工作区打包。

## 信息替换

将模板中的姓名、学号、班级、项目题目和日期替换为需求文件中的真实值；没有依据的个人信息保持待用户补充，不进行猜测。

## 验收策略

项目执行启动和 CRUD 冒烟测试；截图通过人工 VISUAL_STOP；Office 运行 `office_engine.py`/`validate_office.py` 并渲染检查；提交包比较文件夹与 ZIP 清单、扫描敏感文件并逐项映射 R1–R3；最后填写 `delivery_review.json`。
