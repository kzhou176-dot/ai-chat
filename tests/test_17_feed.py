#!/usr/bin/env python3
"""
test_17_feed — aichat-hub Cycle 17 Feed 时间线模块测试
==================================================
覆盖:
  1. 4 类 Feed 分类
  2. 数据模型(Comment / FeedItem)
  3. 30+ 静态 Feed
  4. FeedEngine 核心(list / get / publish / like / comment / share)
  5. 排序(time / hot)
  6. 筛选(category / school / industry)
  7. 个性化推荐(holland_code / industry / school)
  8. 互动(like / unlike / comment)
  9. CLI 入口
  10. 集成
"""
import sys
import subprocess
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from feed import (
    CATEGORIES, CATEGORY_LABELS, FEED_POOL,
    Comment, FeedItem, FeedEngine,
    list_feed, get_post, publish_post,
    like_post, add_comment, share_post,
    recommend_for_user, list_categories,
)


# ============== 1. 4 类 Feed ==============

def test_categories_count():
    """4 类 Feed"""
    assert len(CATEGORIES) == 4
    assert set(CATEGORIES) == {"alumni_post", "industry_post", "career_post", "recruit_post"}
    print("✓ 4 类 Feed")


def test_category_labels():
    """分类标签"""
    for c in CATEGORIES:
        assert c in CATEGORY_LABELS
        label, emoji = CATEGORY_LABELS[c]
        assert label
        assert emoji
    print("✓ 分类标签")


def test_list_categories():
    """列出 4 类"""
    cs = list_categories()
    assert len(cs) == 4
    for c in cs:
        assert "id" in c
        assert "label" in c
        assert "emoji" in c
    print("✓ 列出 4 类")


# ============== 2. 数据模型 ==============

def test_comment_dataclass():
    """Comment"""
    c = Comment(id="C1", author_id="U1", author_name="张三", content="好文!")
    d = c.to_dict()
    assert d["id"] == "C1"
    assert d["author_name"] == "张三"
    print("✓ Comment")


def test_feed_item_basic():
    """FeedItem 基础"""
    f = FeedItem(
        id="F1", author_id="A1", author_name="测试",
        author_role="user", content="hello", category="career_post",
    )
    assert f.likes == 0
    assert f.comments == []
    assert f.shares == 0
    print("✓ FeedItem 基础")


def test_feed_item_to_dict():
    """FeedItem 序列化"""
    f = FeedItem(id="F1", author_id="A1", author_name="测试",
                 author_role="user", content="hello", category="career_post")
    d = f.to_dict()
    assert d["category_label"] == "求职技巧"
    assert d["category_emoji"] == "💼"
    print("✓ FeedItem 序列化")


def test_feed_item_is_liked_by():
    """FeedItem 点赞判断"""
    f = FeedItem(id="F1", author_id="A1", author_name="测试", author_role="user", content="x")
    f.liked_by.append("U1")
    assert f.is_liked_by("U1")
    assert not f.is_liked_by("U2")
    print("✓ 点赞判断")


# ============== 3. 30+ 静态 Feed ==============

def test_feed_pool_count():
    """Feed 池 ≥ 30"""
    assert len(FEED_POOL) >= 30
    print(f"✓ Feed 池 {len(FEED_POOL)} 条")


def test_feed_pool_per_category():
    """每类 ≥ 5"""
    counts = {c: 0 for c in CATEGORIES}
    for f in FEED_POOL:
        counts[f.category] += 1
    for c, cnt in counts.items():
        assert cnt >= 5, f"{c} 数量 = {cnt}"
    print(f"✓ 每类 ≥ 5: {counts}")


def test_feed_pool_required_fields():
    """Feed 必填字段"""
    for f in FEED_POOL:
        assert f.id
        assert f.author_id
        assert f.author_name
        assert f.content
        assert f.category in CATEGORIES
        assert f.timestamp > 0
    print("✓ Feed 必填字段")


def test_feed_pool_unique_ids():
    """Feed ID 唯一"""
    ids = [f.id for f in FEED_POOL]
    assert len(set(ids)) == len(ids)
    print("✓ Feed ID 唯一")


def test_feed_pool_schools_diversity():
    """学校多样性(alumni_post 至少 5+ 学校)"""
    alumni_posts = [f for f in FEED_POOL if f.category == "alumni_post"]
    schools = set(f.author_school for f in alumni_posts if f.author_school)
    assert len(schools) >= 5
    print(f"✓ 校友来自 {len(schools)} 所学校")


def test_feed_pool_industries_diversity():
    """行业多样性(industry_post 至少 5+ 行业)"""
    industry_posts = [f for f in FEED_POOL if f.category == "industry_post"]
    industries = set(f.author_industry for f in industry_posts if f.author_industry)
    assert len(industries) >= 5
    print(f"✓ 行业洞察覆盖 {len(industries)} 行业")


# ============== 4. FeedEngine 核心 ==============

def test_engine_list_feed():
    """列出 Feed"""
    engine = FeedEngine()
    items = engine.list_feed(limit=10)
    assert len(items) == 10
    print("✓ 列出 Feed")


def test_engine_list_feed_filter_category():
    """按分类筛选"""
    engine = FeedEngine()
    items = engine.list_feed(category="alumni_post", limit=5)
    assert all(i["category"] == "alumni_post" for i in items)
    print(f"✓ alumni_post {len(items)} 条")


def test_engine_list_feed_filter_school():
    """按学校筛选"""
    engine = FeedEngine()
    items = engine.list_feed(author_school="清华大学", limit=10)
    assert all(i["author_school"] == "清华大学" for i in items)
    assert len(items) >= 3
    print(f"✓ 清华校友 {len(items)} 条")


def test_engine_list_feed_filter_industry():
    """按行业筛选"""
    engine = FeedEngine()
    items = engine.list_feed(author_industry="互联网", limit=10)
    assert all(i["author_industry"] == "互联网" for i in items)
    print(f"✓ 互联网行业 {len(items)} 条")


def test_engine_list_feed_sort_time():
    """按时间排序"""
    engine = FeedEngine()
    items = engine.list_feed(limit=5, sort="time")
    for i in range(len(items) - 1):
        assert items[i]["timestamp"] >= items[i+1]["timestamp"]
    print("✓ 时间排序")


def test_engine_list_feed_sort_hot():
    """按热度排序"""
    engine = FeedEngine()
    items = engine.list_feed(limit=5, sort="hot")
    for i in range(len(items) - 1):
        score_i = items[i]["likes"] + items[i]["shares"] * 2 + len(items[i]["comments"]) * 3
        score_j = items[i+1]["likes"] + items[i+1]["shares"] * 2 + len(items[i+1]["comments"]) * 3
        assert score_i >= score_j
    print("✓ 热度排序")


def test_engine_get_post():
    """获取单条"""
    engine = FeedEngine()
    post = engine.get_post("FP001")
    assert post is not None
    assert post["id"] == "FP001"
    assert "张学长" in post["author_name"]
    print("✓ 获取单条")


def test_engine_get_post_not_found():
    """未找到"""
    engine = FeedEngine()
    assert engine.get_post("NOTEXIST") is None
    print("✓ 未找到返回 None")


def test_engine_publish():
    """发布"""
    engine = FeedEngine()
    before = len(engine._pool)
    post = engine.publish_post(
        author_id="U1", author_name="小王", author_role="user",
        content="新发布的 Feed", category="career_post", tags=["测试"],
    )
    assert post["id"] is not None
    assert post["content"] == "新发布的 Feed"
    assert len(engine._pool) == before + 1
    print(f"✓ 发布:{post['id']}")


def test_engine_publish_invalid_category():
    """发布无效分类 → fallback"""
    engine = FeedEngine()
    post = engine.publish_post(
        author_id="U1", author_name="x", author_role="user",
        content="x", category="invalid_category",
    )
    assert post["category"] == "career_post"  # fallback
    print("✓ 无效分类 fallback")


def test_engine_like():
    """点赞"""
    engine = FeedEngine()
    result = engine.like_post("FP001", "U1")
    assert "post" in result
    assert result["action"] == "liked"
    assert "U1" in result["post"]["liked_by"]
    assert result["post"]["likes"] >= 1
    print("✓ 点赞")


def test_engine_like_unlike():
    """再点 → unlike"""
    engine = FeedEngine()
    r1 = engine.like_post("FP001", "U1")
    r2 = engine.like_post("FP001", "U1")
    assert r1["action"] == "liked"
    assert r2["action"] == "unliked"
    print("✓ 再点 unlike")


def test_engine_like_not_found():
    """点赞不存在的 post"""
    engine = FeedEngine()
    r = engine.like_post("NOTEXIST", "U1")
    assert "error" in r
    print("✓ 不存在返 error")


def test_engine_comment():
    """评论"""
    engine = FeedEngine()
    r = engine.add_comment("FP001", "U1", "小王", "好文!")
    assert "comment_id" in r
    assert len(r["post"]["comments"]) >= 1
    print("✓ 评论")


def test_engine_comment_not_found():
    """评论不存在"""
    engine = FeedEngine()
    r = engine.add_comment("NOTEXIST", "U1", "x", "x")
    assert "error" in r
    print("✓ 不存在返 error")


def test_engine_share():
    """分享"""
    engine = FeedEngine()
    r = engine.share_post("FP001")
    assert "post" in r
    assert r["post"]["shares"] >= 1
    print("✓ 分享")


# ============== 5. 个性化推荐 ==============

def test_recommend_holland_only():
    """只 Holland Code"""
    recs = recommend_for_user(holland_code="IAS", limit=5)
    assert len(recs) == 5
    print(f"✓ IAS 推荐 {len(recs)} 条")


def test_recommend_industry_only():
    """只行业"""
    recs = recommend_for_user(target_industry="互联网", limit=5)
    assert len(recs) == 5
    print(f"✓ 互联网行业推荐 {len(recs)} 条")


def test_recommend_school_only():
    """只学校"""
    recs = recommend_for_user(user_school="清华大学", limit=5)
    assert len(recs) >= 3  # 清华有多条
    print(f"✓ 清华校友推荐 {len(recs)} 条")


def test_recommend_combined():
    """组合:清华 + 互联网 + IAS"""
    recs = recommend_for_user(
        holland_code="IAS", target_industry="互联网", user_school="清华大学",
        limit=5,
    )
    # Top 1 应有清华 + 互联网 + 校友动态
    top1 = recs[0]
    assert top1["author_school"] == "清华大学" or top1["author_industry"] == "互联网"
    print(f"✓ 组合推荐 Top 1: {top1['author_name']}")


def test_recommend_empty():
    """空推荐参数 → 按热度"""
    recs = recommend_for_user(limit=5)
    assert len(recs) == 5
    print("✓ 空推荐 → 默认 5 条")


def test_recommend_score_higher_for_match():
    """匹配项应在 Top"""
    recs_with = recommend_for_user(target_industry="互联网", limit=30)
    recs_without = recommend_for_user(limit=30)
    # 含互联网参数的 Top 1 应该是互联网相关
    top1 = recs_with[0]
    assert top1["author_industry"] == "互联网" or top1["category"] in ("industry_post", "alumni_post")
    print(f"✓ 推荐 Top 1 是相关: {top1['author_name']}({top1['author_industry']})")


# ============== 6. 模块级 API ==============

def test_module_list_feed():
    """模块级 list_feed"""
    items = list_feed(limit=5)
    assert len(items) == 5
    print("✓ 模块级 list_feed")


def test_module_get_post():
    """模块级 get_post"""
    post = get_post("FP021")
    assert post is not None
    print("✓ 模块级 get_post")


def test_module_publish():
    """模块级 publish_post"""
    post = publish_post(
        author_id="U", author_name="U", author_role="user",
        content="test", category="career_post",
    )
    assert post["id"] is not None
    print("✓ 模块级 publish")


def test_module_like():
    """模块级 like_post"""
    r = like_post("FP002", "test_user")
    assert "post" in r or "error" in r
    print("✓ 模块级 like")


# ============== 7. CLI ==============

def test_cli_list():
    """CLI:list"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "feed.py"), "list"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "FP001" in result.stdout or "张学长" in result.stdout
    print("✓ CLI list")


def test_cli_categories():
    """CLI:categories"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "feed.py"), "categories"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "alumni_post" in result.stdout
    assert "🎓" in result.stdout
    print("✓ CLI categories")


def test_cli_get():
    """CLI:get"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "feed.py"), "get", "FP001"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["id"] == "FP001"
    print("✓ CLI get")


def test_cli_recommend():
    """CLI:recommend"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "feed.py"), "recommend", "IAS", "互联网", "清华大学"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    # 至少应有输出
    assert len(result.stdout) > 0
    print("✓ CLI recommend")


def test_cli_publish():
    """CLI:publish"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "feed.py"), "publish", "CLI测试", "这是CLI测试内容", "career_post"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "发布成功" in result.stdout
    print("✓ CLI publish")


# ============== 8. 集成 ==============

def test_integration_full_flow():
    """集成:发布 → 点赞 → 评论 → 推荐"""
    engine = FeedEngine()
    # 1. 发布
    post = engine.publish_post(
        author_id="U1", author_name="测试用户", author_role="user",
        content="我今天通过了霍兰德测试,代码是 IAS!",
        category="career_post", tags=["霍兰德", "校招"],
        author_school="清华大学", author_industry="互联网",
    )
    pid = post["id"]
    # 2. 点赞
    r = engine.like_post(pid, "U2")
    assert r["action"] == "liked"
    # 3. 评论
    r = engine.add_comment(pid, "U3", "张三", "恭喜!")
    assert "comment_id" in r
    # 4. 推荐(同代码 + 清华 + 互联网)
    recs = engine.recommend_for_user(
        holland_code="IAS", target_industry="互联网", user_school="清华大学", limit=5,
    )
    assert len(recs) == 5
    # 刚发布的应该出现在推荐里(可能在 Top 1,具体取决于排序)
    post_ids = [r["id"] for r in recs]
    assert pid in post_ids, f"新发布应在推荐中,实际 {post_ids}"
    print(f"✓ 集成:发布 → 点赞 → 评论 → 推荐: {pid}")


def test_integration_school_filter_with_recommend():
    """集成:学校筛选 + 推荐"""
    # 清华校友动态 +30(校)+20(行业)+15(holland)+ 热度分
    # 静态池中清华 alumni_post 至少 4 条(FP001/002/003/006)
    # Top 应优先清华,后混入高 likes
    recs = recommend_for_user(user_school="清华大学", limit=5)
    # 严格用 list_feed 筛选
    items = list_feed(author_school="清华大学", limit=10)
    assert all(i["author_school"] == "清华大学" for i in items)
    # 推荐中至少前 3 应是清华
    top3 = recs[:3]
    assert all(r["author_school"] == "清华大学" for r in top3)
    print(f"✓ 清华校友推荐 Top 3 全清华 + 严格筛选 {len(items)} 条")


def test_integration_industry_chain():
    """集成:行业链(行业 → 校友 → 公司)"""
    # 找清华互联网行业校友
    recs = recommend_for_user(
        user_school="清华大学", target_industry="互联网",
        limit=5,
    )
    # Top 1 应该是清华互联网
    top1 = recs[0]
    assert top1["author_school"] == "清华大学"
    assert top1["author_industry"] == "互联网"
    print(f"✓ 清华+互联网 Top 1: {top1['author_name']} → {top1['author_avatar']}")


# ============== 入口 ==============

if __name__ == "__main__":
    test_categories_count()
    test_category_labels()
    test_list_categories()
    test_comment_dataclass()
    test_feed_item_basic()
    test_feed_item_to_dict()
    test_feed_item_is_liked_by()
    test_feed_pool_count()
    test_feed_pool_per_category()
    test_feed_pool_required_fields()
    test_feed_pool_unique_ids()
    test_feed_pool_schools_diversity()
    test_feed_pool_industries_diversity()
    test_engine_list_feed()
    test_engine_list_feed_filter_category()
    test_engine_list_feed_filter_school()
    test_engine_list_feed_filter_industry()
    test_engine_list_feed_sort_time()
    test_engine_list_feed_sort_hot()
    test_engine_get_post()
    test_engine_get_post_not_found()
    test_engine_publish()
    test_engine_publish_invalid_category()
    test_engine_like()
    test_engine_like_unlike()
    test_engine_like_not_found()
    test_engine_comment()
    test_engine_comment_not_found()
    test_engine_share()
    test_recommend_holland_only()
    test_recommend_industry_only()
    test_recommend_school_only()
    test_recommend_combined()
    test_recommend_empty()
    test_recommend_score_higher_for_match()
    test_module_list_feed()
    test_module_get_post()
    test_module_publish()
    test_module_like()
    test_cli_list()
    test_cli_categories()
    test_cli_get()
    test_cli_recommend()
    test_cli_publish()
    test_integration_full_flow()
    test_integration_school_filter_with_recommend()
    test_integration_industry_chain()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
