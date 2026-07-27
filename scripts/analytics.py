#!/usr/bin/env python3
"""
aichat-hub Analytics (用户行为分析) 模块
======================================
从已有数据源(relationship / memory / cost)汇总用户行为指标。

核心指标:
  - 消息数(total / per_user)
  - 活跃天数
  - 关系阶段分布
  - 留存(N 日留存 cohort)
  - 漏斗(关键路径转化率)
  - 价值(累计成本 / 累计消息)

数据源(可插拔):
  - JSON 事件文件
  - 关系记录(relationship.py)
  - 成本记录(cost.py)
  - 内存事件(memory.py)

Cycle 10 - 基础版
"""
from __future__ import annotations
import json
import time
import math
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


@dataclass
class UserEvent:
    """用户行为事件"""
    ts: float  # unix timestamp
    user_id: str
    event_type: str  # message / persona_change / cost / etc
    persona: str = ""
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FunnelStep:
    """漏斗步骤"""
    name: str
    user_count: int
    conversion_rate: float  # 0-1,从上一步


@dataclass
class CohortMetric:
    """Cohort(同期群)指标"""
    cohort: str  # e.g. "2026-07-21"
    size: int  # cohort 大小
    retention: Dict[int, float]  # {N: 留存率}


class Analytics:
    """用户行为分析器"""

    def __init__(self, root: Path = None):
        self.root = root or Path(
            "str(Path(__file__).parent.parent)/data/analytics"
        )
        self.root.mkdir(parents=True, exist_ok=True)
        self.events: List[UserEvent] = []
        self._load()

    def _path(self) -> Path:
        return self.root / "events.json"

    def _load(self):
        path = self._path()
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.events = [UserEvent(**e) for e in data.get("events", [])]
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[analytics] load warning: {e}")

    def save(self):
        data = {
            "events": [asdict(e) for e in self.events],
            "saved_at": time.time(),
        }
        self._path().write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---------- 记录 ----------

    def record(
        self,
        user_id: str,
        event_type: str,
        persona: str = "",
        detail: Dict[str, Any] = None,
        ts: float = None,
    ) -> UserEvent:
        ev = UserEvent(
            ts=ts or time.time(),
            user_id=user_id,
            event_type=event_type,
            persona=persona,
            detail=detail or {},
        )
        self.events.append(ev)
        return ev

    # ---------- 总览 ----------

    def overview(self) -> Dict[str, Any]:
        """总览统计"""
        if not self.events:
            return {
                "total_events": 0,
                "unique_users": 0,
                "unique_personas": 0,
                "time_range": None,
            }
        users = set(e.user_id for e in self.events)
        personas = set(e.persona for e in self.events if e.persona)
        ts_min = min(e.ts for e in self.events)
        ts_max = max(e.ts for e in self.events)
        return {
            "total_events": len(self.events),
            "unique_users": len(users),
            "unique_personas": len(personas),
            "time_range": {
                "start": datetime.fromtimestamp(ts_min).isoformat(),
                "end": datetime.fromtimestamp(ts_max).isoformat(),
                "days": (ts_max - ts_min) / 86400 if ts_max > ts_min else 0,
            },
            "events_per_user": round(len(self.events) / max(1, len(users)), 2),
        }

    def message_count(self, user_id: str = None) -> Dict[str, int]:
        """消息数统计"""
        msgs = [e for e in self.events if e.event_type == "message"]
        if user_id:
            return {user_id: sum(1 for e in msgs if e.user_id == user_id)}
        # 按 user
        cnt = Counter(e.user_id for e in msgs)
        return dict(cnt)

    def active_days(self, user_id: str = None) -> Dict[str, int]:
        """每个用户活跃天数"""
        user_days = defaultdict(set)
        for e in self.events:
            day = datetime.fromtimestamp(e.ts).strftime("%Y-%m-%d")
            user_days[e.user_id].add(day)
        if user_id:
            return {user_id: len(user_days.get(user_id, set()))}
        return {uid: len(days) for uid, days in user_days.items()}

    # ---------- 关系阶段分布 ----------

    def persona_distribution(self) -> Dict[str, int]:
        """按 persona 统计事件数"""
        return dict(Counter(e.persona for e in self.events if e.persona))

    def relationship_stage_dist(self) -> Dict[str, int]:
        """关系阶段分布(从 event detail 中提取)"""
        stages = Counter()
        for e in self.events:
            if e.event_type == "relationship_change":
                stage = e.detail.get("stage", "unknown")
                stages[stage] += 1
        return dict(stages)

    # ---------- 漏斗分析 ----------

    def funnel(
        self,
        steps: List[str],
        user_id: str = None,
    ) -> List[FunnelStep]:
        """漏斗分析:每个步骤独立用户数 + 转化率"""
        if user_id:
            events = [e for e in self.events if e.user_id == user_id]
        else:
            events = self.events

        # 按时间排序
        events = sorted(events, key=lambda e: e.ts)

        # 每个步骤的去重用户集合
        user_sets: List[set] = []
        for step in steps:
            users_in_step = set()
            for e in events:
                if e.event_type == step or e.detail.get("step") == step:
                    users_in_step.add(e.user_id)
            user_sets.append(users_in_step)

        # 计算每步用户数 + 转化率
        result: List[FunnelStep] = []
        prev_count = 0
        for i, (step, users) in enumerate(zip(steps, user_sets)):
            count = len(users)
            if i == 0:
                rate = 1.0
            elif prev_count == 0:
                rate = 0.0
            else:
                rate = count / prev_count
            result.append(FunnelStep(
                name=step, user_count=count, conversion_rate=round(rate, 4)
            ))
            prev_count = count
        return result

    # ---------- Cohort 留存 ----------

    def cohort_retention(
        self,
        cohort_window_days: int = 1,
        retention_days: List[int] = None,
    ) -> List[CohortMetric]:
        """Cohort 留存分析(按天分组)"""
        if retention_days is None:
            retention_days = [1, 3, 7, 14, 30]

        # 按用户首次事件日期分组
        user_first_seen: Dict[str, float] = {}
        for e in self.events:
            if e.user_id not in user_first_seen or e.ts < user_first_seen[e.user_id]:
                user_first_seen[e.user_id] = e.ts

        # 用户按 cohort_date 分组
        cohorts: Dict[str, List[str]] = defaultdict(list)
        for uid, ts in user_first_seen.items():
            cd = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            cohorts[cd].append(uid)

        # 计算每个 cohort 的留存
        results: List[CohortMetric] = []
        for cd, users in sorted(cohorts.items()):
            size = len(users)
            user_set = set(users)
            # 用户事件(按 ts 索引)
            user_events: Dict[str, List[float]] = defaultdict(list)
            for e in self.events:
                if e.user_id in user_set:
                    user_events[e.user_id].append(e.ts)

            # 留存率
            retention = {}
            for n in retention_days:
                retained = 0
                for uid in users:
                    first_ts = user_first_seen[uid]
                    # 在 first_ts + n 天之内是否再次活跃
                    for ts in user_events[uid]:
                        if ts >= first_ts + n * 86400:
                            retained += 1
                            break
                retention[n] = round(retained / max(1, size), 4)
            results.append(CohortMetric(
                cohort=cd, size=size, retention=retention
            ))
        return results

    # ---------- 价值 ----------

    def value_per_user(self) -> Dict[str, Dict[str, float]]:
        """每个用户的价值(消息数 + 成本)"""
        result: Dict[str, Dict[str, float]] = {}
        # 聚合成本
        cost_by_user: Dict[str, float] = defaultdict(float)
        msg_by_user: Dict[str, int] = defaultdict(int)
        for e in self.events:
            if e.event_type == "message":
                msg_by_user[e.user_id] += 1
            elif e.event_type == "cost":
                uid = e.detail.get("user_id", e.user_id)
                cost_by_user[uid] += e.detail.get("cost_usd", 0.0)
        all_users = set(msg_by_user) | set(cost_by_user)
        for uid in all_users:
            msgs = msg_by_user.get(uid, 0)
            cost = cost_by_user.get(uid, 0.0)
            result[uid] = {
                "messages": msgs,
                "cost_usd": round(cost, 6),
                "cost_per_message": round(cost / max(1, msgs), 6),
            }
        return result

    # ---------- 综合报告 ----------

    def report(self) -> Dict[str, Any]:
        """综合报告"""
        return {
            "overview": self.overview(),
            "message_count": self.message_count(),
            "active_days": self.active_days(),
            "persona_distribution": self.persona_distribution(),
            "relationship_stage_dist": self.relationship_stage_dist(),
            "value_per_user": self.value_per_user(),
        }


# ============== /api/analytics endpoint helper ==============

def analytics_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """从 dict 事件生成报告"""
    a = Analytics()
    for e in payload.get("events", []):
        a.events.append(UserEvent(
            ts=e.get("ts", time.time()),
            user_id=e.get("user_id", "unknown"),
            event_type=e.get("event_type", "unknown"),
            persona=e.get("persona", ""),
            detail=e.get("detail", {}),
        ))
    return a.report()


if __name__ == "__main__":
    # demo
    a = Analytics()
    base = time.time() - 86400 * 5  # 5 天前
    # 用户 1:活跃 5 天,共 20 条消息
    for i in range(20):
        day = i // 5
        a.record(
            user_id="user1", event_type="message",
            persona="xiaoai", detail={"tokens": 100},
            ts=base + day * 86400 + i * 3600,
        )
    # 用户 1:1 次关系升级
    a.record(user_id="user1", event_type="relationship_change",
            persona="xiaoai", detail={"stage": "friend", "level": 18},
            ts=base + 86400)
    # 用户 1:1 条成本
    a.record(user_id="user1", event_type="cost",
            detail={"cost_usd": 0.0012, "user_id": "user1"})

    # 用户 2:仅 1 天活跃,3 条消息
    for i in range(3):
        a.record(user_id="user2", event_type="message",
                persona="dr_li", detail={"tokens": 200},
                ts=base + 2 * 86400 + i * 1800)

    a.save()
    print("=== Analytics Report ===\n")
    print(json.dumps(a.report(), ensure_ascii=False, indent=2, default=str))
    print("\n=== Funnel: 5 步 ===")
    funnel = a.funnel(["message", "relationship_change", "cost"])
    for step in funnel:
        print(f"  {step.name:25s} users={step.user_count}  rate={step.conversion_rate:.2%}")
    print("\n=== Cohort Retention ===")
    cohorts = a.cohort_retention(retention_days=[1, 3, 7])
    for c in cohorts:
        print(f"  {c.cohort} (n={c.size}): {c.retention}")
