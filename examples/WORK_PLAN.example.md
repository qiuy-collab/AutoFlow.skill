# AutoFlow Work Plan — 学生选课系统交付

## 目标

基于用户需求完成可运行的学生选课系统，提供真实页面证据、Word 报告和只包含规定文件的提交包。验收以核心 CRUD 可运行、证据与实现一致、文档模板完整为准。

## 工作流

使用 custom DAG：`task.research → SOURCE_STOP → task.build → image.capture → VISUAL_STOP → word.fill → package.assemble → DELIVERY_STOP`。GitHub 候选由用户决定；系统、截图、文档和压缩包分别执行运行、视觉、结构和清单校验。

## 产物

- `project.source`：改造后的项目目录和上游归属说明。
- `task.result`：启动命令、测试命令、功能验证和 changed files 摘要。
- `image.assets`：用户批准的真实页面截图。
- `word.document`：填写后的课程设计报告。
- `package.bundle`：按要求生成的提交压缩包。

## 范围与约束

只实现需求列出的学生、课程和选课 CRUD；不新增支付、云部署或无关营销页面。保留模板结构，不使用伪造运行截图，不在用户选择前克隆候选，不把缓存、密钥或整个工作区打包。
