# 移动端 PWA + i18n 设计调研(2024-2026)

> Cycle 20 调研,支撑 `scripts/mobile.py` 设计
> 用途:为 AIchat-Hub 提供移动端适配 + 国际化基础

---

## 1. 大学生移动端使用情况

### 数据(2024-2025)
- 大学生 90%+ 优先用手机(非 PC)
- App 下载意愿低(空间/流量限制)
- **PWA 渗透率高**:小红书 / 微博 / Twitter / Telegram 都有 PWA 版本
- 多语言需求:中国大学生英语水平参差,英文资料需求也强

---

## 2. PWA 三大核心

### 2.1 Web App Manifest
- `manifest.json`:app name / icons / theme_color / display
- 让浏览器"添加到主屏幕"时呈现 App 体验
- 不需要 App Store / Google Play

### 2.2 Service Worker
- 离线缓存(offline-first)
- 后台同步 / Push 通知
- 沙箱友好可选(纯本地项目不需要)

### 2.3 响应式 CSS
- `@media (max-width: 600px)` 移动端样式
- 触摸优化(按钮 44x44px 最小)
- 横竖屏适配
- 字体/间距放大

---

## 3. i18n 主流方案

| 方案 | 模式 | 适合 |
|---|---|---|
| **gettext(.po/.mo)** | 编译时 | 传统 C/Python 项目 |
| **i18next(JSON)** | 运行时 | JS / 前端 |
| **自建 dict** | 简单 | 小型项目 / API |
| **Flask-Babel** | 集成 | Flask Web |
| **polib** | Python .po 解析 | 跨平台 |

我们选**自建 dict**:
- 项目无前端框架(纯 HTML/JS)
- Python 端 API 用 dict 即可
- 轻量,无依赖

---

## 4. AIchat-Hub `scripts/mobile.py` 设计要点

### 4.1 PWA Manifest
- `manifest.json`:完整 manifest(name/short_name/icons/theme_color/display)
- 通过 `GET /api/mobile/manifest` 提供

### 4.2 mobile.css
- 响应式样式(基于 cycle 19 dashboard)
- 触摸优化(按钮 44x44)
- 横竖屏适配
- iOS 安全区域(env(safe-area-inset-*))

### 4.3 i18n 字典
- `translations` dict:`{"zh-CN": {...}, "en-US": {...}}`
- 关键字符串覆盖(API 名称 / 状态 / 错误)
- 简单 lookup,无 fallback chain

### 4.4 移动端 API 优化
- 列表分页(默认 limit=10,可调)
- payload 压缩(省略冗余字段)
- ETag / Cache-Control(可选)

### 4.5 沙箱安全
- manifest + CSS + dict 全静态
- 无 Service Worker(本地项目,沙箱友好)

---

## 5. 字符串覆盖(20+ 关键)

### 通用
- "服务运行中" / "Service running"
- "请求错误" / "Bad request"
- "未找到" / "Not found"
- "内部错误" / "Internal error"

### 模块
- "虚拟人" / "Persona"
- "简历" / "Resume"
- "面试" / "Interview"
- "职业规划" / "Career"
- "行业" / "Industry"
- "校友" / "Alumni"
- "数字虚拟人" / "Digital Human"
- "Feed" / "Feed"
- "Prompt 模板" / "Prompt Templates"
- "Dashboard" / "Dashboard"

### 状态
- "已完成" / "Completed"
- "进行中" / "In progress"
- "失败" / "Failed"

---

## 6. PWA manifest 字段

```json
{
  "name": "AIchat-Hub",
  "short_name": "AIchat-Hub",
  "description": "中国大学生职业社交 + 数字虚拟人",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#667eea",
  "theme_color": "#667eea",
  "icons": [
    {
      "src": "/static/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

---

## 7. 数据来源

- Google PWA 文档
- MDN Web App Manifest
- Apple PWA 规范
- 微信小程序 PWA 兼容
- 2024 移动端 Web 性能报告

---

**[CYCLE_20_DONE]** — Cycle 20 调研完成:`scripts/mobile.py` 设计就绪
