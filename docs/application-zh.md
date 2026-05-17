# MiMo 100T Token 申请 — OmniMemo

## 项目描述（申请表填写用）

OmniMemo — 基于 MiMo 全栈的多模态会议智能体

利用 MiMo V2.5 的 100 万 token 上下文窗口，一次性载入完整 2-4 小时会议全文（8-15万字），实现跨时段议题追踪、发言人关联和决策溯源——这是传统 32K 上下文方案无法做到的。

传统方案需要把会议切成小块分别处理再拼接，丢失了跨时段的上下文关联（例如"上半场讨论的 API 方案"与"下半场确认的最终决策"之间的关联）。OmniMemo 利用 MiMo 的 1M 上下文窗口，将完整会议记录作为单一上下文输入，保留所有跨时段关联。

MiMo 全栈协同：
- MiMo-V2.5-Omni：原生统一处理音频+视频+截图+文本，无需拼接多个 API pipeline
- MiMo-V2.5-Pro：深度推理提取决策点、行动项、争议焦点，支持跨时段议题追踪
- MiMo-V2.5-TTS：3 分钟语音回顾 1 小时会议，中英双语自然语音摘要

技术栈：Python 3.10+, Click CLI, OpenAI SDK, pytest (28 tests), GitHub Actions CI
开发工具：Cursor + Claude Code
已开源：https://github.com/ohh561/OmniMemo

---

## AI Tools Used

- Cursor (主要开发工具)
- Claude Code (代码审查和重构)

## Base Model Series

- MiMo (主要)
- Claude (原型验证)
- DeepSeek (原型验证)

---

## 截图清单（申请上传用）

1. GitHub 仓库首页（README 渲染效果）
2. GitHub Pages 网站 (docs/index.html)
3. `pytest -v` 通过的终端截图
4. `omni-memo info` CLI 输出截图
5. `omni-memo stats examples/sample_meeting.txt` 截图（展示 1M 上下文检测）

---

## 提交前检查清单

- [ ] Email 匹配 MiMo 平台账号
- [ ] 如果平台用手机号注册，先在 id.mi.com 绑定邮箱
- [ ] 截图格式 JPG/PNG，每个 < 20MB
- [ ] 项目描述详细具体
- [ ] 项目描述明确提到 MiMo 的差异化能力（1M 上下文窗口）
