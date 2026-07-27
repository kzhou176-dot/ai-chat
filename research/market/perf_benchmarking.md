# 性能基准测试市场调研 (2026-07-21)

## 调研背景
v1.0.1 收尾优化阶段,需要给 74 个 web endpoint 出一个**性能基线报告**,
证明 stdlib (http.server) 方案在不同负载下的响应能力。

## 行业现状 (2026)

### 主流 HTTP 性能测试工具
| 工具 | 协议 | 优缺点 |
|---|---|---|
| **wrk** | HTTP/1.1 | C 写,高并发,无依赖。stdlib 场景用不上 |
| **k6** | HTTP/1.1+ | JS 脚本,云原生,需要 runtime |
| **ab (Apache Bench)** | HTTP/1.1 | 老牌,功能简单 |
| **locust** | HTTP 全 | Python 写,需额外装包 |
| **hey** | HTTP/2 | Go 写,简单粗暴 |
| **vegeta** | HTTP/2 | Go 写,可视化好 |

**结论**:生产环境用 wrk/k6,沙箱/演示环境用 **stdlib 自写** 即可,本项目目标。

### Python stdlib 性能测试基线指标
- **冷启动**:http.server 启动 ~0.1-0.3s
- **静态 JSON endpoint**: < 5ms
- **带 DB 模拟**: < 20ms
- **带 LLM mock 调用**: < 50ms
- **总并发**:BaseHTTPServer 单线程,~50 req/s;ThreadingHTTPServer ~200 req/s

### 行业 benchmark 报告范式
1. **响应时间分布**: p50 / p95 / p99 / max
2. **吞吐量**: req/s,successful vs failed
3. **资源占用**: CPU% / RSS memory
4. **错误率**: timeout / 5xx / connection refused
5. **冷启动 vs 热路径**: 首次请求 / 稳态

## 对 aichat-hub 的启示

### 74 个 endpoint 分类性能预期
- **纯静态枚举** (人设/角色/学校列表): p95 < 2ms
- **规则计算** (简历评分/匹配): p95 < 10ms
- **session 管理** (interview/chat start/end): p95 < 15ms
- **含 LLM mock 错误路径** (chat/synthesize): p95 < 5ms (无 LLM 立即返)
- **检索 + 排序** (paper search/feed recommend): p95 < 20ms

### benchmark 模块设计原则
1. **不依赖外部网络**:全部 localhost
2. **不依赖 LLM**:mock fallback 已就绪
3. **可重复**:seed 控制随机性
4. **生成可视化报告**:JSON + Markdown + 简单 ASCII 表
5. **沙箱友好**:无 pip install,纯 stdlib

## v1.0.1 benchmark 目标

- `scripts/benchmark.py` 提供:
  - `run_endpoint(url)` 单次请求 + 计时
  - `run_endpoint_n(url, n=100)` 多次统计
  - `benchmark_all(endpoints)` 批量跑
  - `percentile(times, p)` p50/p95/p99
  - `generate_report(results)` 输出 md 报告
  - `BenchmarkResult` 数据类
- `tests/test_24_benchmark.py` 覆盖 30+ 断言

## 产出
- `research/market/perf_benchmarking.md` (本文件)
- `scripts/benchmark.py` (~12KB)
- `tests/test_24_benchmark.py` (~7KB)
- `data/benchmark_report.json` (运行结果)
- `reports/benchmark_report.md` (人类可读报告)
