# 2D 数字虚拟人(角色化形象)横评(2024-2026)

> Cycle 16 调研,支撑 `scripts/digital_human.py` 设计
> 用途:为大学生虚拟人形象(角色化 2D Live)功能提供设计基线

---

## 1. 数字虚拟人分类

### 按技术形态
| 形态 | 代表 | 优缺点 | 适合 |
|---|---|---|---|
| **2D Live** | Live2D / VTube Studio | 轻量、可爱、可互动 | 二次元 / 内容创作 / 陪伴 |
| **2D 卡通** | Midjourney + Live2D | 灵活、风格多 | 品牌 / 营销 |
| **3D 高保真** | HeyGen / Synthesia / 商汤如影 | 真实、贵 | 企业 / 客服 |
| **3D 二次元** | UE5 / VRoid | 沉浸、可玩 | 游戏 / 直播 |
| **3D 数字分身** | 苹果 Memoji / Ready Player Me | 个人化、轻 | 社交 / 教学 |

### 按应用场景
- **陪伴 / 情感**:Replika / 星野 / Talkie(2D Live 偏多)
- **教学 / 答疑**:Knewton / 多邻国(2D 卡通)
- **面试 / 求职**:InterviewBit AI(2D 卡通)
- **客服 / 销售**:HeyGen / Synthesia(3D 高保真)
- **直播 / 营销**:VTuber / 抖音 AI 数字人(2D Live / 3D 二次元)

---

## 2. 大学生虚拟人需求

### 需求 1:形象个性化
- 选头像(发型/服装/风格)
- 选性格(温柔/理性/幽默)
- 与"我是谁"挂钩(角色化)

### 需求 2:情感表达
- 不只是文字,要有表情/动作
- 根据对话内容自动切换表情(happy/sad/surprised)
- 动作配合(wave / nod / thinking)

### 需求 3:多场景复用
- 同一个虚拟人在不同场景表现不同
- 模拟面试时严肃,陪伴时温柔
- 切换 persona 不需要换形象

### 需求 4:低成本可商用
- 大学生预算低(0 元)
- 沙箱友好(无 GPU / 无 API)
- 但要有"可用"的形象

---

## 3. 主流工具对比

| 工具 | 2D/3D | 风格 | 大学生友好 | 价格 |
|---|---|---|---|---|
| **Live2D Cubism** | 2D | 二次元 | ★★★ | 免费(个人) / Pro ¥1000+ |
| **VTube Studio** | 2D Live | 二次元 | ★★★★ | 免费 + Pro $5/月 |
| **VRoid Studio** | 3D 二次元 | 二次元 | ★★★★ | 免费 |
| **Ready Player Me** | 3D 卡通 | 通用 | ★★★★ | 免费 |
| **HeyGen** | 3D 高保真 | 真人 | ★★(英文) | $24/月 |
| **Synthesia** | 3D 高保真 | 真人 | ★★(英文) | $22/月 |
| **商汤如影** | 3D 高保真 | 真人 | ★★★(企业) | 企业定价 |
| **剪映数字人** | 3D 真人 | 真人 | ★★★★ | 免费(短) |
| **即梦 AI 数字人** | 3D 真人 | 真人 | ★★★★ | 免费 |
| **Live2D + AI 驱动** | 2D Live | 二次元 | ★★★ | 需自接 |

---

## 4. 共性短板(我们能补的)

### 短板 1:静态形象,无动态交互
- 多数工具做"形象生成",不做"角色化对话联动"
- 虚拟人不知道自己在什么场景(面试 / 陪伴 / 教学)

### 短板 2:无与 AIchat-Hub 模块联动
- 形象是孤立的,不和 persona / memory / scene 联动
- 我们已经做了 11+ 角色(Persona + Industry + Interview + Career + Alumni),需要"形象 + 角色"统一

### 短板 3:大学生角色单一
- 商业数字人偏"销售/客服",不是"学长学姐/面试官/职业规划师"
- 缺乏"过来人""引路人"角色

### 短板 4:无沙箱模式
- 大多数工具需要 API key / GPU
- 沙箱环境无 key 也能跑(返回元数据)

---

## 5. AIchat-Hub `scripts/digital_human.py` 设计要点

### 5.1 数字虚拟人(角色化)
- **基础属性**:名字 / 性别 / 年龄 / 风格(anime/realistic/cartoon/2d_live)
- **外观描述**:发型 / 服装 / 配色 / 体型(纯文字描述,不实际生成图片)
- **表情库**:6 基础表情(happy/sad/angry/surprised/fearful/neutral)
- **动作库**:6 基础动作(wave/nod/shake_head/bow/point/clap)
- **状态机**:idle / listening / speaking / thinking / reacting

### 5.2 多角色预设(7+ 角色)
- **小爱**(xiaoai) 🌸 — 情感陪伴 / 暖心学姐
- **李医生**(dr_li) ⚕️ — 资深 HR 顾问
- **小智**(xiaozhi) 🤖 — 互联网行业专家
- **面试官**(interviewer) 💼 — 4 角色复用(tech/behavioral/hr/pressure)
- **职业规划师**(career_guide) 🧭 — 霍兰德导师
- **行业专家**(industry_expert) 🏢 — 9 行业复用
- **学长学姐**(senior) 🎓 — 校友数字分身

### 5.3 状态联动
```python
# 角色对话时,虚拟人状态自动切换
when user_message:
    state = "listening"
when generating_response:
    state = "thinking"
when streaming:
    state = "speaking", expression = "neutral"
when user_says "great!":
    state = "reacting", expression = "happy", action = "wave"
```

### 5.4 复用现有模块
- **avatar_video.py**(cycle 6):4 provider 抽象,作为底层渲染
- **persona.py**(cycle 1):Persona 数据类,提供性格/记忆
- **interview.py**(cycle 12):4 面试官 Prompt
- **career_profile.py**(cycle 13):职业规划师 Prompt
- **industry_insight.py**(cycle 14):9 行业专家 Prompt
- **alumni.py**(cycle 15):4 学长学姐 Prompt

### 5.5 沙箱安全
- 不实际生成图片/视频(返回元数据 + 描述)
- 表情/动作/状态用 enum 表达
- 外观描述用纯文本(可后续接 SD/Midjourney)

---

## 6. 表情 / 动作 / 状态词典

### 6 基础表情
| ID | 中文 | Emoji | 触发场景 |
|---|---|---|---|
| happy | 开心 | 😊 | 用户答对/好消息 |
| sad | 难过 | 😢 | 用户沮丧/失败 |
| angry | 生气 | 😠 | 压力面/质疑 |
| surprised | 惊讶 | 😮 | 新信息/意外 |
| fearful | 紧张 | 😰 | 模拟面试紧张 |
| neutral | 中性 | 😐 | 默认 / 思考 |

### 6 基础动作
| ID | 中文 | 触发场景 |
|---|---|---|
| wave | 挥手 | 欢迎/再见 |
| nod | 点头 | 同意/理解 |
| shake_head | 摇头 | 不同意 |
| bow | 鞠躬 | 感谢/尊重 |
| point | 指向 | 强调重点 |
| clap | 鼓掌 | 鼓励/庆祝 |

### 5 状态
| ID | 中文 | 含义 |
|---|---|---|
| idle | 待机 | 等待用户 |
| listening | 听 | 用户输入中 |
| thinking | 思考 | AI 生成中 |
| speaking | 说 | AI 回复中 |
| reacting | 反应 | 触发表情/动作 |

---

## 7. 数据来源

- Live2D Cubism 官网
- VTube Studio 官网
- VRoid Studio 官网
- 剪映 / 即梦 AI 数字人产品说明
- Replika / 星野 数字人形象研究
- 36氪《2024 数字人产业白皮书》

---

**[CYCLE_16_DONE]** — Cycle 16 调研完成:`scripts/digital_human.py` 设计就绪
