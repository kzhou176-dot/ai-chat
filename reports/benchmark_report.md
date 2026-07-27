# AICHAT-HUB 端点性能基准报告 (v1.0.1)

生成时间: 2026-07-21 17:44:45

**总端点数**: 74
**总错误数**: 0
**每端点请求数**: 20

## 🏆 Top 10 最快 (按 p95 排序)

| 排名 | Method | Path | p50 (ms) | p95 (ms) | p99 (ms) | mean (ms) |
|---|---|---|---|---|---|---|
| 1 | POST | `/api/avatar` | 0.00 | 0.00 | 0.00 | 0.00 |
| 2 | GET | `/` | 0.00 | 0.00 | 0.00 | 0.00 |
| 3 | GET | `/api/resume/variants` | 0.00 | 0.00 | 0.00 | 0.00 |
| 4 | POST | `/api/career/profile` | 0.00 | 0.00 | 0.00 | 0.00 |
| 5 | POST | `/api/career/answer` | 0.00 | 0.00 | 0.00 | 0.00 |
| 6 | POST | `/api/industry/recommend` | 0.00 | 0.00 | 0.00 | 0.00 |
| 7 | GET | `/api/human/meta` | 0.00 | 0.00 | 0.00 | 0.00 |
| 8 | POST | `/api/industry/answer` | 0.00 | 0.00 | 0.00 | 0.00 |
| 9 | GET | `/api/career/codes` | 0.00 | 0.00 | 0.00 | 0.00 |
| 10 | POST | `/api/alumni/refer/status` | 0.00 | 0.00 | 0.00 | 0.00 |

## 🐌 Top 10 最慢 (按 p95 排序)

| 排名 | Method | Path | p50 (ms) | p95 (ms) | p99 (ms) | mean (ms) |
|---|---|---|---|---|---|---|
| 1 | GET | `/api/feed/list` | 0.45 | 0.47 | 0.49 | 0.46 |
| 2 | GET | `/api/human/list` | 0.27 | 0.50 | 0.54 | 0.30 |
| 3 | POST | `/api/feed/recommend` | 0.28 | 0.51 | 0.57 | 0.33 |
| 4 | GET | `/api/prompt/search` | 0.57 | 0.58 | 0.58 | 0.57 |
| 5 | GET | `/api/alumni/list` | 0.60 | 0.63 | 0.71 | 0.60 |
| 6 | GET | `/api/prompt/list` | 0.52 | 0.69 | 0.85 | 0.55 |
| 7 | GET | `/api/papers/list` | 1.09 | 1.18 | 1.55 | 1.14 |
| 8 | GET | `/api/release/notes` | 1.28 | 1.61 | 1.69 | 1.34 |
| 9 | GET | `/api/release/readiness` | 1.96 | 2.73 | 3.66 | 2.12 |
| 10 | GET | `/api/release/stats` | 3.74 | 4.33 | 4.44 | 3.84 |

## 📊 分类汇总

| 类别 | 端点数 | p50 均值 | p95 均值 | p99 均值 |
|---|---|---|---|---|
| core | 1 | 0.00 | 0.00 | 0.00 |
| api/personas | 1 | 0.05 | 0.27 | 0.88 |
| api/voices | 1 | 0.02 | 0.22 | 3.17 |
| api/chat | 1 | 0.07 | 0.16 | 0.83 |
| api/compare | 1 | 0.02 | 0.08 | 0.11 |
| api/synthesize | 1 | 0.05 | 0.12 | 0.12 |
| api/avatar | 2 | 0.05 | 0.19 | 0.52 |
| api/analytics | 1 | 0.03 | 0.10 | 0.99 |
| api/cost | 1 | 0.03 | 0.07 | 0.60 |
| api/score | 1 | 0.05 | 0.09 | 0.56 |
| api/resume | 5 | 0.00 | 0.02 | 0.28 |
| api/interview | 4 | 0.00 | 0.04 | 0.57 |
| api/career | 5 | 0.00 | 0.02 | 0.21 |
| api/industry | 6 | 0.03 | 0.05 | 0.37 |
| api/alumni | 5 | 0.15 | 0.19 | 0.58 |
| api/human | 6 | 0.05 | 0.11 | 0.34 |
| api/feed | 7 | 0.11 | 0.16 | 0.38 |
| api/prompt | 6 | 0.18 | 0.23 | 0.43 |
| api/dashboard | 1 | 0.01 | 0.03 | 0.23 |
| api/mobile | 4 | 0.00 | 0.01 | 0.04 |
| api/papers | 6 | 0.24 | 0.32 | 1.05 |
| api/paper_chat | 3 | 0.01 | 0.05 | 0.36 |
| api/release | 5 | 1.40 | 1.74 | 1.98 |

## 📋 全量列表 (按 path 字母排序)

| Method | Path | p50 (ms) | p95 (ms) | mean (ms) | errors |
|---|---|---|---|---|---|
| GET | `/` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/alumni/list` | 0.60 | 0.63 | 0.60 | 0 |
| POST | `/api/alumni/match` | 0.15 | 0.17 | 0.15 | 0 |
| POST | `/api/alumni/refer` | 0.01 | 0.01 | 0.01 | 0 |
| POST | `/api/alumni/refer/status` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/alumni/schools` | 0.00 | 0.13 | 0.13 | 0 |
| GET | `/api/analytics` | 0.03 | 0.10 | 0.09 | 0 |
| POST | `/api/avatar` | 0.00 | 0.00 | 0.00 | 0 |
| POST | `/api/avatar/tts` | 0.10 | 0.39 | 0.19 | 0 |
| POST | `/api/career/answer` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/career/codes` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/career/dimensions` | 0.00 | 0.07 | 0.07 | 0 |
| POST | `/api/career/profile` | 0.00 | 0.00 | 0.00 | 0 |
| POST | `/api/career/start` | 0.01 | 0.02 | 0.01 | 0 |
| POST | `/api/chat` | 0.07 | 0.16 | 0.12 | 0 |
| POST | `/api/compare` | 0.02 | 0.08 | 0.03 | 0 |
| GET | `/api/cost` | 0.03 | 0.07 | 0.06 | 0 |
| GET | `/api/dashboard/meta` | 0.01 | 0.03 | 0.02 | 0 |
| GET | `/api/feed/categories` | 0.00 | 0.10 | 0.10 | 0 |
| POST | `/api/feed/comment` | 0.01 | 0.01 | 0.01 | 0 |
| POST | `/api/feed/like` | 0.01 | 0.01 | 0.01 | 0 |
| GET | `/api/feed/list` | 0.45 | 0.47 | 0.46 | 0 |
| GET | `/api/feed/post` | 0.00 | 0.01 | 0.00 | 0 |
| POST | `/api/feed/publish` | 0.03 | 0.04 | 0.03 | 0 |
| POST | `/api/feed/recommend` | 0.28 | 0.51 | 0.33 | 0 |
| POST | `/api/human/create` | 0.03 | 0.03 | 0.03 | 0 |
| GET | `/api/human/list` | 0.27 | 0.50 | 0.30 | 0 |
| GET | `/api/human/meta` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/human/presets` | 0.00 | 0.09 | 0.09 | 0 |
| POST | `/api/human/react` | 0.00 | 0.00 | 0.00 | 0 |
| POST | `/api/human/render` | 0.00 | 0.01 | 0.00 | 0 |
| POST | `/api/industry/answer` | 0.00 | 0.00 | 0.00 | 0 |
| POST | `/api/industry/ask` | 0.13 | 0.18 | 0.17 | 0 |
| GET | `/api/industry/list` | 0.01 | 0.10 | 0.10 | 0 |
| GET | `/api/industry/profile` | 0.00 | 0.01 | 0.00 | 0 |
| POST | `/api/industry/recommend` | 0.00 | 0.00 | 0.00 | 0 |
| POST | `/api/industry/start` | 0.01 | 0.02 | 0.01 | 0 |
| POST | `/api/interview/answer` | 0.00 | 0.00 | 0.00 | 0 |
| POST | `/api/interview/end` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/interview/interviewers` | 0.00 | 0.08 | 0.08 | 0 |
| POST | `/api/interview/start` | 0.01 | 0.08 | 0.07 | 0 |
| GET | `/api/mobile/css` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/mobile/i18n` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/mobile/languages` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/mobile/manifest` | 0.00 | 0.01 | 0.01 | 0 |
| POST | `/api/paper_chat/ask` | 0.00 | 0.01 | 0.00 | 0 |
| POST | `/api/paper_chat/end` | 0.00 | 0.01 | 0.01 | 0 |
| POST | `/api/paper_chat/start` | 0.01 | 0.15 | 0.08 | 0 |
| GET | `/api/papers/cite` | 0.01 | 0.01 | 0.01 | 0 |
| GET | `/api/papers/get` | 0.01 | 0.01 | 0.01 | 0 |
| GET | `/api/papers/keywords` | 0.01 | 0.01 | 0.01 | 0 |
| GET | `/api/papers/list` | 1.09 | 1.18 | 1.14 | 0 |
| POST | `/api/papers/search` | 0.20 | 0.32 | 0.23 | 0 |
| GET | `/api/papers/stats` | 0.13 | 0.40 | 0.39 | 0 |
| GET | `/api/personas` | 0.05 | 0.27 | 0.11 | 0 |
| GET | `/api/prompt/categories` | 0.00 | 0.07 | 0.07 | 0 |
| GET | `/api/prompt/get` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/prompt/list` | 0.52 | 0.69 | 0.55 | 0 |
| POST | `/api/prompt/render` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/prompt/search` | 0.57 | 0.58 | 0.57 | 0 |
| GET | `/api/prompt/summary` | 0.01 | 0.01 | 0.01 | 0 |
| GET | `/api/release/notes` | 1.28 | 1.61 | 1.34 | 0 |
| GET | `/api/release/readiness` | 1.96 | 2.73 | 2.12 | 0 |
| GET | `/api/release/stats` | 3.74 | 4.33 | 3.84 | 0 |
| POST | `/api/release/tag` | 0.00 | 0.03 | 0.01 | 0 |
| GET | `/api/release/tags` | 0.01 | 0.02 | 0.01 | 0 |
| POST | `/api/resume/generate` | 0.00 | 0.01 | 0.00 | 0 |
| GET | `/api/resume/personas` | 0.00 | 0.09 | 0.09 | 0 |
| POST | `/api/resume/rewrite` | 0.00 | 0.00 | 0.00 | 0 |
| POST | `/api/resume/score` | 0.00 | 0.00 | 0.00 | 0 |
| GET | `/api/resume/variants` | 0.00 | 0.00 | 0.00 | 0 |
| POST | `/api/score` | 0.05 | 0.09 | 0.08 | 0 |
| POST | `/api/synthesize` | 0.05 | 0.12 | 0.06 | 0 |
| GET | `/api/voices` | 0.02 | 0.22 | 0.21 | 0 |

## ✅ 结论

- ✅ 所有端点 0 错误 100% 成功
- 📊 全局平均 p95: **0.23 ms**
- 🎯 最快端点 p95: **0.00 ms**
- 🐢 最慢端点 p95: **4.33 ms**