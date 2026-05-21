# OmniMemo — 多模态会议智能体

> 基于小米 MiMo V2.5 全栈模型（Pro + Omni + TTS）的智能会议理解与摘要系统
>
> 利用 MiMo 的 **100 万 token 上下文窗口**，一次性处理完整会议记录，保留跨时段关联

<p align="center">
  <img src="https://img.shields.io/badge/MiMo_V2.5-1M_Context-blue" />
  <img src="https://img.shields.io/badge/Python-3.10+-green" />
  <img src="https://img.shields.io/badge/Tests-28_passed-brightgreen" />
  <img src="https://img.shields.io/badge/CI-GitHub_Actions-orange" />
  <img src="https://img.shields.io/badge/License-MIT-blue" />
</p>

---

## 🎯 为什么需要 100 万 token 上下文？

一场 2 小时的会议，转写文本约 3-5 万字（~5-7 万 token）。传统方案需要切片处理，**丢失跨时段的议题关联和发言人追踪**。

OmniMemo 利用 MiMo V2.5 的 **1,000,000 token 上下文窗口**，一次性载入完整 4-6 小时会议记录，实现：

- **跨时段议题追踪**："上半场讨论的 API 方案" ↔ "下半场确认的最终决策"
- **发言人全局关联**：同一发言人在不同时段的观点对比
- **决策溯源**：从提议→讨论→争议→共识的完整链条

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🎙️ 多模态输入 | 会议录音、视频、截图、白板照片 |
| 🧠 跨模态理解 | MiMo-Omni 原生统一处理音频+视频+图像+文本 |
| 📝 结构化纪要 | 自动提取决策点、行动项、争议焦点，分层输出 |
| 🔊 语音摘要 | MiMo-TTS 生成 3 分钟语音回顾 1 小时会议 |
| 🤖 智能调度 | 自动识别会议类型，匹配最佳分析模板 |
| 📊 长上下文 | 100 万 token 窗口，处理完整 4-6 小时会议 |

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      OmniMemo Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│  📁 输入: 录音/视频/截图/白板/转写文本                       │
│       ↓                                                      │
│  🧠 MiMo-Omni (跨模态理解)                                  │
│     原生统一处理 音频+视频+图像+文本                          │
│     自动利用 1M 上下文窗口处理长文档                          │
│       ↓                                                      │
│  🤖 Agent 调度器 (会议类型识别 → 分析模板选择)               │
│       ↓                                                      │
│  🧠 MiMo-Pro (深度推理)                                      │
│     发言人识别 → 决策提取 → 行动项生成 → 争议标注             │
│       ↓                                                      │
│  🔊 MiMo-TTS (语音播报)                                      │
│     结构化纪要 → 3 分钟自然语音摘要                           │
│       ↓                                                      │
│  📤 输出: Markdown 纪要 + JSON 数据 + 语音摘要               │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/ohh561/OmniMemo.git
cd OmniMemo
pip install -e ".[dev]"
```

### 配置

```bash
cp .env.example .env
# 编辑 .env，填入 MiMo API Key
```

### 使用

```bash
# 查看配置信息
omni-memo info

# 查看文件 token 统计（演示 1M 上下文优势）
omni-memo stats examples/sample_meeting.txt

# 处理会议文件，生成结构化纪要
omni-memo process examples/sample_meeting.txt --format markdown

# 处理并生成语音摘要
omni-memo process meeting.txt --voice -o ./output

# 识别会议类型
omni-memo classify meeting.txt
```

### 示例输出

```bash
$ omni-memo stats examples/sample_meeting.txt

┌──────────────────────────────────────┐
│ 文件: examples/sample_meeting.txt     │
│ 预估 Token: ~68,000                  │
│ 需要 1M 上下文: ✔ 是                 │
└──────────────────────────────────────┘

$ omni-memo process examples/sample_meeting.txt

╭──── 会议纪要 ────────────────────────────╮
│ # Q2 产品路线图规划会                     │
│ **参会人**: 张三、李四、王五、赵六、孙七  │
│                                          │
│ ## ✅ 决策                               │
│ - Q2 核心方向: 用户增长 + 技术债务并行    │
│ - 数据平台: Q2 调研设计, Q3 全面实施      │
│                                          │
│ ## 🎯 行动项                             │
│ - [high] 张三: 支付模块方案评审           │
│ - [high] 李四: 支付模块拆分第一阶段       │
╰──────────────────────────────────────────╯
```

## 🛠️ 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 跨模态理解 | MiMo-V2.5-Omni | 原生多模态处理 |
| 深度推理 | MiMo-V2.5-Pro | 决策/行动项提取 |
| 语音合成 | MiMo-V2.5-TTS | 中英双语语音摘要 |
| 开发工具 | Cursor + Claude Code | AI 辅助开发 |
| 后端框架 | Python 3.10+ / Click / Rich | CLI 工具 |
| API 客户端 | OpenAI SDK | MiMo API 兼容 |
| 测试 | pytest (28 tests) | 单元 + 集成测试 |
| CI/CD | GitHub Actions | Python 3.10/3.11/3.12 |

## 📊 Token 消耗预估

| 场景 | 单次消耗 | 月度目标 | 月度总量 |
|------|---------|---------|---------|
| 1h 会议（多模态） | ~15-20 万 Token | 200+ 场 | 3000-4000 万 Token |
| 语音摘要生成 | ~5-10 万 Token | 200+ 场 | 1000-2000 万 Token |
| 多轮追问交互 | ~3-5 万 Token | 500+ 次 | 1500-2500 万 Token |
| **月度总计** | - | - | **5500-8500 万 Token** |

## 📁 项目结构

```
OmniMemo/
├── omni_memo/              # 核心包
│   ├── cli.py              # CLI 入口 (Click)
│   ├── config.py           # 配置管理
│   ├── pipeline.py         # 端到端处理流水线
│   ├── omni/processor.py   # MiMo-Omni 跨模态理解
│   ├── pro/analyzer.py     # MiMo-Pro 深度推理
│   ├── tts/generator.py    # MiMo-TTS 语音合成
│   ├── agent/dispatcher.py # Agent 调度器
│   └── utils/              # 工具 (chunker, formatter)
├── tests/                  # 测试套件 (28 tests)
├── examples/               # 演示样本
├── artifacts/              # 示例输出
├── docs/index.html         # GitHub Pages 网站
├── .github/workflows/ci.yml # CI 配置
└── pyproject.toml          # 项目元数据
```

## 🧪 运行测试

```bash
pytest -v
# 28 passed in 0.81s
```

## 🚀 发展路线

- ✅ **Phase 1 (MVP)**: CLI + Omni/Pro/TTS 模块 + 测试 + CI
- 📋 **Phase 2 (V1.0)**: Web 界面 + 用户认证 + 多会议类型模板
- 📋 **Phase 3 (V2.0)**: 实时会议转录 + 团队协作 + 历史分析
- ✅ **Phase 4 (V2.0)**: 多语言 + 移动端 + 生态集成（钉钉/飞书）

## 📄 License

MIT

## 🔗 相关链接

- [MiMo 官网](https://mimo.xiaomi.com/)
- [MiMo API 开放平台](https://platform.xiaomimimo.com/)
- [MiMo 100T Token 申请](https://100t.xiaomimimo.com/)
- [项目网站](https://ohh561.github.io/OmniMemo)
