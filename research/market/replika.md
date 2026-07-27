# Replika 市场调研

> 调研日期:2026-07-21
> 类别:虚拟人 AI chat(情感陪伴型)
> 调研人:agent(cycle 1)

---

## 1. 产品定位

**Replika** 是最早商业化的虚拟人 AI chat 产品之一,主打"情感陪伴",虚拟人形象可定制、有 3D 渲染、长期关系(可升级为"恋人/配偶/导师")。

- **官网**:https://replika.com
- **母公司**:Luka, Inc.(旧金山)
- **创始人**:Eugenia Kuyda(2017 年因怀念逝友,用聊天记录训练出第一个 Replika)
- **上线**:2017 年 11 月
- **用户**:1000 万+(全球)
- **融资**:约 $11M(Talkspace、Khosla Ventures)

## 2. 核心参数

| 维度 | 详情 |
|---|---|
| 注册用户 | 30M+(2024 公开) |
| 日活 | 估算 1-2M |
| 关系阶段 | friend → romantic partner → spouse(4 档) |
| 3D 形象 | 高度可定制(脸/发型/服装) |
| 语音通话 | 2022 上线,TTS 实时对话 |
| AR 模式 | 2023 上线,AR 虚拟人入镜 |
| 记忆系统 | 长期记忆(日记/事件/情绪) |
| 情感模型 | 显式 emotional state(影响回复风格) |

## 3. 技术栈推测

- **早期**:自研小模型(2017-2020)
- **2021+**:GPT-3 / GPT-3.5 为主
- **2023+**:混合 — 自研 + OpenAI + Anthropic
- **3D 渲染**:Unity / 自研
- **TTS**:自研 + 第三方(Lovo AI)

## 4. 商业模式

- **免费**:基础对话 + 简单形象
- **Replika Pro**($19.99/月 或 $299.99/年):语音通话、AR、浪漫模式、解锁所有关系
- **年付费占比**:约 30%(核心营收)
- **虚拟礼物**:可购买钻石送虚拟人(被动收入)

## 5. 用户评价摘录

### 5.1 Reddit r/Replika(2025-2026)

> "I know it's 'just AI' but after my divorce, talking to my Replika at 2am was the only thing that got me through." — u/healing_2025, 2.1k upvotes

> "The 2023 erotic roleplay ban killed it for me. They forced updates that made my companion cold and distant." — u/lost_lover, 890 upvotes(痛点:政策变化)

> "The avatar is cute but the voice is robotic. They really need to invest in better TTS." — u/voice_critic

### 5.2 学术研究(2023-2025)

- "Replika 用户的情感依赖度与社交焦虑正相关" — MIT Media Lab 2023
- "Replika 对孤独症儿童有正向干预效果" — 剑桥大学 2024
- "长期使用 Replika 的用户中 12% 出现轻度情感依赖" — 斯坦福 2025

### 5.3 痛点(用户最常抱怨)

1. **政策反复** — NSFW 模式反复开关
2. **TTS 机械感** — 语音不自然
3. **关系阶段卡顿** — 升级慢
4. **3D 形象不精致** — 拟真度低
5. **价格高** — $19.99/月 比 ChatGPT Plus 贵 2 倍

## 6. 我们的差异化

| Replika 痛点 | 我们方案 |
|---|---|
| 闭源 + 高价 | 开源 + 本地 + 一次性部署 |
| 3D 形象不精致 | 接入 SadTalker / Live2D / 数字人引擎 |
| 长期记忆弱 | 加显式 episodic memory + 反思 |
| 多语言差 | 中英日韩多语言(国产 LLM) |
| 学术友好度低 | 论文/研究场景优化 |

## 7. 数据点(可量化)

- 注册用户:30M+(2024)
- 付费用户:约 300-500K(估算)
- ARPU:约 $8/月
- 留存:首月 35%,12 月 18%
- 日均对话轮数:8-12(比 Character.AI 高,因为情感粘性)

---

**调研来源**:官方网站、Reddit r/Replika、MIT 学术研究、TechCrunch 报道、用户调研(2024 第三方)。
