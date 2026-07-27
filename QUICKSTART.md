# aichat-hub v1.0.2 — 快速使用

## 🎉 当前状态

✅ **Server 正在运行**

- PID: 83759
- URL: **http://127.0.0.1:8765**
- 26/26 endpoint 烟雾测试通过
- Log: `~/Library/Logs/aichat-hub/launcher.log`

---

## 🚀 3 种使用方式

### 方式 1:macOS GUI(已装到 /Applications)

```bash
# 双击 .app(Finder)
open /Applications/aichat-hub.app

# 或 Spotlight: 搜 "aichat-hub"
```

会自动弹通知 + 打开浏览器到 http://127.0.0.1:8765

### 方式 2:命令行 `aichat`(推荐)

```bash
# 加到 PATH(只需一次)
echo 'export PATH="$HOME/.mavis/agents/mavis/workspace/aichat-hub/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 然后任意位置:
aichat start        # 启动
aichat status       # 状态
aichat test         # 烟雾测试
aichat open         # 开浏览器
aichat stop         # 停止
aichat logs         # 看日志
aichat demo         # 端到端 demo
aichat benchmark    # 性能基准
```

### 方式 3:从源码(任何时候都有效)

```bash
cd /Users/yuefeng/.mavis/agents/mavis/workspace/aichat-hub
python3 scripts/web.py
# 然后浏览器打开 http://127.0.0.1:8765
```

---

## 🎮 试玩

打开 http://127.0.0.1:8765 之后,有几个推荐入口:

| URL | 看点 |
|---|---|
| `/api/dashboard/html` | 静态 HTML dashboard(15KB 单页) |
| `/api/personas` | 3 个虚拟人列表 |
| `/api/papers/list?keyword=llm` | 60 篇 arxiv 论文 |
| `/api/alumni/list` | 30 个校友(同校同院同专业) |
| `/api/career/dimensions` | 霍兰德 6 维度 |

## 🐚 cURL 示例

```bash
# 看 personas
curl http://127.0.0.1:8765/api/personas

# 搜论文
curl -X POST http://127.0.0.1:8765/api/papers/search \
  -H "Content-Type: application/json" \
  -d '{"query":"LLM","limit":3}'

# 校友匹配
curl -X POST http://127.0.0.1:8765/api/alumni/match \
  -H "Content-Type: application/json" \
  -d '{"school":"清华","major":"CS","industry":"互联网"}'

# v1.0.2 发布就绪检查
curl http://127.0.0.1:8765/api/release/readiness
```

## 🛠 故障排除

| 现象 | 解决 |
|---|---|
| 端口 8765 已被占用 | `aichat stop` 或 `lsof -i :8765 -t \| xargs kill -9` |
| 浏览器打不开 | 确认 `aichat status` 显示 Running,或访问 `http://127.0.0.1:8765/` |
| .app 双击没反应 | 看 `~/Library/Logs/aichat-hub/launcher.log` |
| Python 找不到 | `brew install python3`(macOS) |
| LLM 报错 | 编辑 `/etc/aichat-hub/config.env`(Linux) 或 `export OPENAI_API_KEY=...`(macOS) |

## 📦 已打好的包

```
/Users/yuefeng/.mavis/agents/mavis/workspace/aichat-hub/dist/
├── aichat-hub-1.0.2-arm64.dmg          (macOS 安装镜像,780KB)
├── aichat-hub_1.0.2_arm64.deb          (Linux ARM64,294KB)
├── aichat-hub_1.0.2_armhf.deb          (Linux ARMv7,294KB)
├── aichat-hub_1.0.2_amd64.deb          (Linux x86_64,294KB)
└── aichat-hub_1.0.2_all.deb            (跨架构,294KB)

/Applications/aichat-hub.app             (macOS app,已装,2MB)
```

要发给别人?给个 `.dmg` 就行。
