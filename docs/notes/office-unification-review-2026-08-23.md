# Office 架构转型复盘：word/ppt/excel 合并 + officecli 后端

> 决策复盘笔记（非契约文档）。记录 2026-08-23 对 `dccc116`（unify document ops on officecli）这次架构转型的评估。
> 背景：作者当时未理清利弊即完成转化，事后希望确认这次转变是否正确、效果上有无区别。

## 1. 事实对比（仓库证据）

| 维度 | 旧架构（合并前，`dccc116^`） | 新架构（现在） |
|---|---|---|
| Word 后端 | `integrations/minimax-docx`：内嵌 .NET 程序（OpenXML SDK 3.2.0，本地 dotnet 编译运行） | `officecli` 二进制（1.0.144，Proprietary，来自 d.officecli.ai） |
| PPT 后端 | `integrations/presentation-skill`：Node.js + pptxgenjs 生成，python-pptx QA，LibreOffice/PPT COM 渲染 | 同一 `officecli` |
| Excel | **不存在** | `officecli`（新增能力） |
| 依赖数量 | dotnet SDK + NuGet + Node.js + pptxgenjs + python-pptx + LibreOffice/COM ≈ 六套技术栈 | 单个二进制 |
| 校验链 | word: XSD 子集（aesthetic/business-rules）+ 预览回退模式 | `office_engine.py`（officecli validate + view issues）+ `validate_office.py`（**纯 Python 独立校验器，不依赖 officecli**） |
| 知识资产 | ~2 万行 OpenXML 参考资料、XSD 规则、CJK 中文排版规范、公文 GB/T 9704、高校模板指南 | officecli 英文 help（help 即 schema），本地化知识资产已删除 |
| 许可/可审计性 | MIT，源码入库，可审计、可改、可离线构建 | Proprietary 闭源，不可审计，安装需联网下载 |

状态记录：2026-08-23 测试 89/89 通过；本机 officecli 1.0.144 已安装；集成包 manifest 固定 revision 1.0.144。

## 2. 评估一：这次架构转变是否正确

### ✅ 做对的部分

1. **依赖从六套技术栈降到单个二进制**——对 AutoFlow 的"能力检测 → blocked 门禁 → 环境报告"模型是数量级简化；Excel 能力从无到有，能力面不降反升（透视表、图表、条件格式、公式重写）。
2. **校验链独立于引擎**（最关键的判断）——`validate_office.py` 自己解 zip、查关系断裂、占位符、模板结构保持、PPT 标题唯一性，不信任 officecli。"可验证交付"底线保住。
3. **Agent 使用体验真实变好**——help 即 schema、稳定 ID 寻址（`shape[@id=...]`）、batch 原子回滚、resident mode。
4. **工程执行质量高**——固定 revision、版本检测诚实（缺失报 blocked 而非静默替代）、CHANGELOG 完整、测试全绿。

### ⚠️ 代价与风险

1. **闭源黑盒依赖（架构性风险）**——产物可验证，但引擎本身不可验证；供应商消失即能力消失。与产品"可验证/审计"定位存在张力。
2. **供应链攻击面扩大**——`curl | bash` / `irm | iex` 安装模式；每次新环境需联网下载；离线/内网不可用。旧 presentation-skill"任务中永不安装依赖"的原则被放弃。
3. **中文排版知识资产被整体删除（真实退化）**——CJK 排版规范、公文 GB/T 9704、高校模板指南属于领域知识，本可脱离后端保留，却与旧实现一起删除。中文文档排版质量保障从"规则引擎 + 知识库"退化为"agent 自己记得多少"。
4. **视觉审查依赖 officecli 自带渲染器**——headless 浏览器渲染，无法用第二个独立渲染器交叉验证。

### 结论

- 作为"通用交付引擎"：**方向正确**。工程执行质量高，校验底线保住。
- 作为"可审计的本地能力"：**退步**。用不可审计的引擎换掉了可审计的引擎。
- 真正的遗憾不是选 officecli，而是**知识资产与实现一起被删除**——二者正交，本可只删实现、保留知识。

## 3. 评估二：officecli 与纯后端在实现效果上的区别

### 效果上限：officecli 全面占优

| 能力 | 旧 Word（.NET） | 旧 PPT（pptxgenjs） | 新 officecli |
|---|---|---|---|
| 动画/转场 | — | 无 | 15+16 种动画预设、Morph/p15、motion-path |
| SmartArt/3D/音视频 | — | 无 | SmartArt、model3d、video/audio、方程 |
| 图表 | 无图表命令 | 基础图表 | 全家族（pieOfPie、barOfPie、pareto、轴动画） |
| 表格/透视表/条件格式 | 表格保留（不生成） | 简单表格 | Excel 全量：透视表、数据验证、CF、sparkline |
| 复杂结构 | 段落/样式/页眉页脚/TOC | 形状/文本 | L3 raw XML + dump→batch 全量往返 |
| 中文排版属性 | 有知识 + 有工具 | — | 工具支持 `font.latin/ea/cs`、`lang.ea/cs`，知识缺失 |

### 效果基线的确定性：旧"规则驱动" → 新"agent 驱动"，方差变大

- 旧：XSD 子集校验 + 预设样式资产（academic/corporate/default）+ 操作手册 → 下限高、风格一致。
- 新：officecli 只保证 schema 合法 + issues 清空，"好看"无兜底，效果取决于 agent 的操作水平。上限高，方差大。

### 中文排版效果：实打实的退化

- 旧：CJK 规范、公文版式、模板指南在知识库，执行前有据可查。
- 新：help 是英文，工具支持 CJK 属性但"该设什么值"的知识没了。

### 视觉审查真实性：旧"外部裁决" → 新"自证"

- 旧：LibreOffice / PowerPoint COM 渲染——真实办公软件裁决，可信度高。
- 新：`officecli view html --browser`——渲染引擎是 officecli 自己实现的，自证问题。

### 文件兼容性（在 Word/WPS 中打开的效果）

- 旧 Word：官方 OpenXML SDK 生成，兼容性有微软背书。
- 新：闭源实现，validate 通过为自报；Schema 合法 ≠ 在 WPS/Office 中渲染正常。**无测试覆盖**。

### 效果 bug 的可修性

- 旧：读 C# 代码直接修，DiffCommand 可对比前后。
- 新：提交 issue 等上游，修复权不在自己手里。

### 效果结论

| 效果维度 | 谁更好 |
|---|---|
| 效果上限/能力广度 | officecli 明显更好 |
| 效果一致性/下限 | 旧架构更好（规则驱动） |
| 中文排版效果 | 旧架构更好（知识资产） |
| 视觉审查可信度 | 旧架构更好（外部裁决 vs 自证） |
| 兼容性风险 | 旧架构更低（官方 SDK vs 闭源） |

**效果上不是简单"更好"，而是"上限换下限"**：拿"更丰富的可能"换掉了"更稳定的保证"，视觉裁决权和兼容性验证都交给了同一个黑盒。

## 4. 建议的补救措施（按优先级）

1. **恢复中文排版知识资产**——从 git 历史（`dccc116^`）捞回 CJK 排版、公文规范、模板指南等，作为 `integrations/cjk-office-knowledge/`（knowledge-only 包），不绑定后端。
2. **写风险接受文档**——`integrations/officecli/UPSTREAM.md` 记录闭源、供应链安装模式、单一供应商锁定，以及回退路线（LibreOffice headless / python-docx）。
3. **加强独立审计层**——validate_office.py 已独立，可再加不依赖 officecli 的内容抽查（openpyxl/python-docx 二次读取关键单元格/段落），交叉验证黑盒输出。
4. **可选：A/B 实测**——同一输入（中文实验报告模板 + PPT 大纲），`git worktree` 检出 `dccc116^` 跑旧架构，对比产物在 WPS/Office 中的实际效果，为上述结论留下实证。

## 5. 待办状态

- [ ] （未开始）恢复中文排版知识资产
- [ ] （未开始）写 officecli 风险接受文档
- [ ] （未开始）独立审计层内容抽查
- [ ] （未开始）A/B 实测（用户当时仅想了解，未要求执行）

> 记录日期：2026-08-23 · 评估人：Ravi + NewMax 助手
