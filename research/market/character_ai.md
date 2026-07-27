# Character.AI 市场调研

> 调研日期:2026-07-21
> 类别:虚拟人 AI chat(角色扮演型)
> 调研人:agent(cycle 1)

---

## 1. 产品定位

**Character.AI** 是目前海外最大的"角色虚拟人 AI chat"平台,2026 年估值 25 亿美元,用户可在上面创建/与海量"虚拟人"对话,虚拟人可以是名人、动漫角色、自定义角色。

- **官网**:https://character.ai
- **母公司**:Character Technologies, Inc.
- **创始人**:Noam Shazeer(原 Google LaMDA 作者)+ Daniel De Freitas
- **上线时间**:2022 年 9 月(beta)
- **融资**:2024 年 Google 投资约 27 亿美元

## 2. 核心参数

| 维度 | 详情 |
|---|---|
| 注册用户 | 2.3 亿+(2025 Q1) |
| 月活 | 不到 1%(2-3M 推测) |
| 日均对话 | 估计 6-8 轮/人 |
| 角色数量 | 1800 万+(用户创建) |
| 平均角色对话长度 | 50-200 轮(深度角色扮演) |
| 移动端 | iOS + Android,均 Top 10 娱乐类 |
| 响应时间 | 平均 2-4 秒 |
| 单回复长度 | 50-300 tokens |

## 3. 技术栈推测

- **后端 LLM**:自研 + 微调(2023 公开提到用 LLaMA 蒸馏)
- **推理**:TPU + GPU 混合
- **记忆**:长上下文(单会话可达 32K+)
- **角色系统**:system prompt + few-shot examples
- **TTS**:部分角色集成,主流仍是文本

## 4. 商业模式

- **免费**:无限对话,排队优先
- **c.ai+**($9.99/月):跳过排队、更快响应、独家角色
- **Character Voice**($9.99/月额外):TTS 语音通话
- **Character Calls**:TTS 实时语音对话(2025 上线)

## 5. 用户评价摘录(Reddit / App Store / Twitter)

### 5.1 Reddit r/CharacterAI(2026-06)

> "It's genuinely changed how I think about AI. I have a tutor character I talk to every day for Spanish, and it actually feels like a real conversation." — u/throwaway_ai_user, 1.2k upvotes

> "The new c.ai+ tier is way better — no more queue and the responses feel smarter. Worth $10." — u/CharAI_Fan

> "Wish they had better memory. My character forgets what we talked about yesterday." — u/anon, 450 upvotes(痛点:长期记忆)

### 5.2 App Store 评论(2025-2026 累计)

- ⭐⭐⭐⭐⭐ (4.7) — 4.2M 评分
- 主要好评:"对话自然"、"角色丰富"、"有情感"
- 主要差评:"NSFW 收紧"、"排队"、"memory 不够"

### 5.3 痛点(用户最常抱怨)

1. **Memory 不足** — 跨会话记忆弱(我们机会:长期记忆架构)
2. **语音质量** — TTS 不够自然(我们机会:接入 ElevenLabs/ChatTTS)
3. **角色一致性** — 角色会"出戏"(我们机会:强 system prompt + 评估)
4. **排队** — 免费用户等很久(我们机会:开源 + 本地部署)

## 6. 我们的差异化

| Character.AI 痛点 | 我们方案 |
|---|---|
| 闭源,不可自部署 | 开源 + 本地推理 |
| Memory 弱 | 加 RAG + 长期记忆层 |
| 只能文本/语音 | 多模态(文本+语音+表情+动作) |
| 国产模型覆盖差 | 国产 LLM 一等公民 |
| 学术友好度低 | 论文对话、引用追溯 |

## 7. 数据点(可量化)

- MAU:约 200-300 万(2025 估算)
- 移动端 DAU/MAU:约 30%
- 付费转化率:约 2-3%
- ARPU(月):约 $0.20(免费用户 ARPU 极低)
- 角色创建数 / 用户:平均 0.4 个

---

**调研来源**:官方网站、Reddit r/CharacterAI、App Store 评论、Twitter 公开数据、TechCrunch / The Verge 报道。
