# aichat-hub v1.0.2 Release Notes

> 🎉 **25 cycle 收官 / 第一个稳定公开版**
> 推送时间: 2026-07-27

## 累计统计

| 指标 | 数量 |
|---|---|
| Python 脚本 | 26 |
| 测试文件 / 通过率 | 27 / 838 (100% pass) |
| Web API 端点 | 74 |
| 代码行数 | ~13K |
| 市场调研 | 28 篇 |
| arxiv 论文 | 60 篇 |
| Prompt 模板 | 32 |
| 角色 | 8 预设 + 4 面试 + 9 行业 + 4 学长 |
| LLM Providers | 6 (OpenAI / DeepSeek / 智谱 / 通义 / Moonshot / Anthropic) |
| 语言 | 2 (zh-CN + en-US) |
| 性能基线 | 74 endpoint p95 mean 0.23ms |
| 协议 | MIT |

## 安装包

| 平台 | 文件 | 大小 |
|---|---|---|
| **Linux(任意架构)** | `aichat-hub_1.0.2_all.deb` | 305K |
| **Linux x86_64** | `aichat-hub_1.0.2_amd64.deb` | 305K |
| **Linux ARM64** (Raspberry Pi 4/5, AWS Graviton) | `aichat-hub_1.0.2_arm64.deb` | 305K |
| **Linux ARMv7** (Raspberry Pi 2/3) | `aichat-hub_1.0.2_armhf.deb` | 305K |
| **macOS Apple Silicon** | `aichat-hub-1.0.2-arm64.dmg` | 832K |
| **macOS .app bundle** | 源码 `packaging/build_macos.sh` 重建 | 2.0MB |

## 快速开始

### Linux
```bash
sudo dpkg -i aichat-hub_1.0.2_all.deb
aichat-hub                   # 启动 :8765
```

### macOS
```bash
open aichat-hub-1.0.2-arm64.dmg
# 拖到 /Applications,双击启动
```

### 源码
```bash
git clone https://github.com/kzhou176-dot/ai-chat.git
cd ai-chat
python3 scripts/web.py
```

## 新功能

### 5 阶段端到端 demo (38 step 100% 通过)
- 职业画像(霍兰德测试)→ 简历(3 角色生成)→ 模拟面试(4 面试官)→ 校友(4 维匹配)→ 论文(60 篇索引)

### 交互式 REPL
- `aichat chat` 启动命令行对话(无浏览器,无服务器)
- 3 角色(小爱 / 李医生 / 小智),8 个内嵌命令

### 真·桌面 GUI (tkinter aqua)
- `aichat desktop` 或 `open /Applications/aichat-hub.app`
- 侧边栏 persona + 聊天气泡 + 异步 chat + 历史持久化

### 性能基准
- `python3 scripts/benchmark.py run` — 74 endpoint 全测,p95 报告

### 端到端冒烟
- `python3 scripts/e2e_demo.py all` — 5 阶段 38 step 验证

## 主要改进

- ✅ 26 个独立模块,每个 < 30K LOC,职责单一
- ✅ 完整测试体系(单元 + 集成 + 性能 + 端到端)
- ✅ 跨平台打包(4 种 DEB 架构 + macOS DMG/.app)
- ✅ 沙箱安全(无 LLM key 也能跑 mock 响应)
- ✅ 标准库 only(无 pip install 依赖,部署轻量)
- ✅ 完整中文文档(README / CHANGELOG / MASTER_PLAN / QUICKSTART / ADMIN_GUIDE)

## 已知限制

- macOS 桌面 app 需要 Python 3.12+(系统自带 3.9 的 Tk 8.5 在 macOS 15 崩溃)
- DEB 包在 macOS 上不能直接安装(架构不匹配)
- arxiv 论文 PDF 未打包(只 JSON 元数据,3.3MB → 240KB)

## 反馈

- 💬 [Discussions](https://github.com/kzhou176-dot/ai-chat/discussions)
- 🐛 [Issues](https://github.com/kzhou176-dot/ai-chat/issues)
- 📖 [管理员手册](docs/ADMIN_GUIDE.md)

## 致谢

历时 25 周期(2026-07-21 至 2026-07-21),由 `kzhou176-dot` 维护。
