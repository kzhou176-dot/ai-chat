# aichat-hub · GitHub 仓库管理员操作手册

> **仓库**:`kzhou176-dot/ai-chat` <https://github.com/kzhou176-dot/ai-chat>
> **默认分支**:`main`
> **协议**:MIT
> **管理员**:`@kzhou176-dot`
> **手册版本**:v1.0.2(配套 aichat-hub v1.0.2)

---

## 0. 30 秒速览

| 操作 | 命令 / 路径 |
|---|---|
| 看 CI 状态 | `.github/workflows/test.yml` |
| 默认分支保护 | `main` 必须 PR + 1 approval + CI 通过 |
| 推送 tag | `git tag v1.0.2 && git push --tags` |
| 触发 release | GitHub Actions 自动(`.github/workflows/release.yml`) |
| 跑测试 | `python3 -m pytest tests/ -v` |
| 部署文档 | `gh-pages` 分支(自动) |

---

## 1. 仓库基础设置(Settings)

### 1.1 必填
- ✅ **Repository name**:`ai-chat`
- ✅ **Default branch**:`main`
- ✅ **Description**:`中国大学生职业领英替代 + 数字虚拟人框架`
- ✅ **Website**:`https://aichat-hub.local`(可选)
- ✅ **Topics**:`python, chatbot, virtual-human, education, llm, tkinter, openai, deepseek`
- ✅ **Features**:
  - ☑ Issues
  - ☑ Pull requests
  - ☑ Discussions
  - ☑ Wiki
  - ☐ Projects(可选)
  - ☑ Sponsorship(可选)
- ✅ **Merge button**:启用 **Squash merge** 为主,Rebase merge 备选

### 1.2 安全(必做)
- ☑ **Private vulnerability reporting**:启用
- ☑ **Dependency graph**:启用
- ☑ **Dependabot alerts**:启用
- ☑ **Dependabot security updates**:启用
- ☑ **Secret scanning**:启用(公开仓库)
- ☑ **Push protection**:启用(阻止 secret 误提交)
- ☐ **Code scanning (CodeQL)**:推荐启用

### 1.3 危险区(确认后再开)
- ☐ **Allow auto-merge**:可开(节省管理员时间)
- ☐ **Automatically delete head branches**:✅ 推荐开
- ☐ **Allow fork PRs from contributors**:✅ 公开仓库必须开

---

## 2. 分支策略

### 2.1 分支命名约定
| 前缀 | 用途 | 例 |
|---|---|---|
| `main` | 稳定主分支(只读,PR 合并) | — |
| `dev` | 开发主线(可选) | — |
| `feature/<name>` | 新功能 | `feature/paper-search` |
| `fix/<issue>` | 修 bug | `fix/arxiv-404` |
| `release/<version>` | 发版准备 | `release/v1.0.3` |
| `hotfix/<critical>` | 紧急修复 | `hotfix/security-x` |

### 2.2 Branch Protection Rules(对 `main`)

**Settings → Branches → Add rule → Branch name pattern: `main`**

✅ **必勾**:
- ☑ **Require a pull request before merging**
  - ☑ Require approvals:**1**
  - ☑ Dismiss stale pull request approvals when new commits are pushed
  - ☑ Require review from Code Owners
- ☑ **Require status checks to pass before merging**
  - ☑ Require branches to be up to date before merging
  - ☑ 必选 status checks:`test / Run pytest`(见 §5)
- ☑ **Require conversation resolution before merging**
- ☑ **Require linear history**(可选,但推荐)
- ☑ **Do not allow force pushes**
- ☑ **Do not allow deletions**
- ☑ **Allow specified actors to bypass required pull requests**:`@kzhou176-dot`(管理员本人)

### 2.3 CODEOWNERS 文件

**位置**:`.github/CODEOWNERS`

```
# aichat-hub 仓库所有者
# 详细语法:https://docs.github.com/zh/codeowners

# 全局默认
*                       @kzhou176-dot

# 核心模块(需双 owner review)
/scripts/                @kzhou176-dot
/tests/                  @kzhou176-dot
/packaging/              @kzhou176-dot

# 文档(任一 owner 可)
/docs/                   @kzhou176-dot
/*.md                    @kzhou176-dot
```

---

## 3. 标签(Tags)& 发布(Releases)

### 3.1 标签规范(SemVer)

```
v<major>.<minor>.<patch>
v<major>.<minor>.<patch>-rc.<n>     # 预发布
v<major>.<minor>.<patch>-alpha.<n>  # 内测
```

例:
- `v1.0.2` — 稳定版
- `v1.0.3-rc.1` — 候选版
- `v2.0.0-alpha.1` — 大版本内测

### 3.2 创建 tag 并推送

```bash
# 本地创建
git tag -a v1.0.2 -m "Release v1.0.2 - 25 cycle 收官"

# 推送
git push origin v1.0.2

# 推送所有 tag
git push --tags

# 列所有 tag
git tag -l
```

### 3.3 在 GitHub 创建 Release

**两种方式**:

**方式 A**:网页手动(适合一次)
1. 访问 `https://github.com/kzhou176-dot/ai-chat/releases/new`
2. **Choose a tag**:`v1.0.2`
3. **Release title**:`v1.0.2 - 25 Cycle 收官`
4. **Description**:
   ```markdown
   ## 🎉 aichat-hub v1.0.2

   ### 累计
   - 26 scripts / 27 tests / 838 tests pass
   - 60 篇 arxiv / 28 篇市场调研
   - 74 HTTP API / 6 LLM providers / 2 languages

   ### 安装
   | 平台 | 文件 |
   |---|---|
   | Linux (any) | `aichat-hub_1.0.2_all.deb` |
   | Linux ARM64 | `aichat-hub_1.0.2_arm64.deb` |
   | macOS Apple Silicon | `aichat-hub-1.0.2-arm64.dmg` |
   ```
5. 勾 ☑ **Set as the latest release**
6. **Attach binaries**:拖拽 `dist/*.deb` 和 `dist/*.dmg`
7. **Publish release**

**方式 B**:CLI(适合 CI)
```bash
gh release create v1.0.2 \
  --title "v1.0.2 - 25 Cycle 收官" \
  --notes-file RELEASE_NOTES.md \
  dist/aichat-hub_1.0.2_all.deb \
  dist/aichat-hub_1.0.2_arm64.deb \
  dist/aichat-hub_1.0.2_armhf.deb \
  dist/aichat-hub_1.0.2_amd64.deb \
  dist/aichat-hub-1.0.2-arm64.dmg
```

### 3.4 预发布(Pre-release)
- alpha / beta / rc 版本 **不要勾** "Set as the latest"
- GitHub Actions 自动判断(看 tag 后缀)

---

## 4. Issue & PR 模板

### 4.1 Issue 模板

**位置**:`.github/ISSUE_TEMPLATE/`

| 文件 | 触发 | 用途 |
|---|---|---|
| `bug_report.md` | 🐛 Bug report | 用户报 bug |
| `feature_request.md` | ✨ Feature request | 新功能建议 |
| `question.md` | ❓ Question | 使用问题 |
| `config.yml` | — | 模板选择器配置 |

### 4.2 PR 模板

**位置**:`.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## 变更类型
- [ ] Bug fix(非破坏性)
- [ ] New feature(非破坏性)
- [ ] Breaking change(会影响现有功能)
- [ ] Documentation only

## 变更内容
<!-- 简述改了什么 -->

## 测试
- [ ] 本地跑通 `python3 -m pytest tests/ -v`
- [ ] 新功能有测试 (`tests/test_<N>_<name>.py`)
- [ ] 没破坏现有功能(全 838+ tests 通过)

## 关联 Issue
Closes #

## 截图(如有)
```

---

## 5. CI / CD(GitHub Actions)

### 5.1 现有 workflow(本仓库应配)

**`.github/workflows/test.yml`** — 每个 PR + push 到 main 触发
**`.github/workflows/release.yml`** — push `v*` tag 触发
**`.github/workflows/docs.yml`** — push 到 main 时自动生成 API 文档

### 5.2 必需 Secrets
**Settings → Secrets and variables → Actions → New repository secret**

| Name | Value | 用途 |
|---|---|---|
| 无需 | — | 项目无外部依赖,纯 stdlib |

(如果以后接入 LLM API key 真实测试,加 `OPENAI_API_KEY` 等)

### 5.3 必需 Variables
**Settings → Secrets and variables → Actions → Variables tab**

| Name | Value | 用途 |
|---|---|---|
| `PYTHON_VERSION` | `3.13` | CI 用 Python 版本 |

### 5.4 本地测试 workflow
```bash
# 安装 act(本地跑 GitHub Actions)
brew install act

# 跑 test workflow
act -j test

# 跑特定 workflow
act workflow_dispatch -W .github/workflows/test.yml
```

---

## 6. 协作者与权限

### 6.1 角色矩阵

| 角色 | 权限 | 适用 |
|---|---|---|
| **Admin** | 全部 | `@kzhou176-dot`(本人) |
| **Maintain** | 管理 issue/PR/release,不能改危险设置 | 核心贡献者 |
| **Write** | push branch,开 PR | 普通贡献者 |
| **Triage** | 看不推送,管理 issue | 社区维护者 |
| **Read** | 只读 | 公开仓库无关 |

**建议**:
- 项目早期:Admin(本人)+ 几个 Maintain(技术负责人)
- 公开后:接受 PR,但不直接给 Write,先 Triage

### 6.2 添加协作者
**Settings → Collaborators → Add people**

### 6.3 团队(Team)
**建议**:`@aichat-hub/maintainers` `@aichat-hub/contributors` `@aichat-hub/robots`

---

## 7. 安全 / Token 管理

### 7.1 ⚠️ Token 使用原则

| 原则 | 描述 |
|---|---|
| **最小权限** | token 只给必要的 scope(例:`repo` 够用就别加 `admin:org`) |
| **短期** | 设 expiration(90 天),到期再换 |
| **轮换** | 怀疑泄漏立即 revoke 旧的,生成新的 |
| **不落盘** | 永远不存 `~/.git-credentials` / `.env` / shell history |
| **不传参** | 命令行 inline,不走 env var(部分 CI 平台会 log env) |

### 7.2 Token 类型
| 场景 | Token 类型 | Scope |
|---|---|---|
| 本地推 GitHub | PAT (Classic) | `repo` |
| CI 推 release | Fine-grained PAT | `contents: write` |
| 自动发 issue | GitHub App(推荐) | — |

### 7.3 推荐做法(本项目)
```bash
# 临时 token,只本次 push 用,绝不存任何地方
GIT_TOKEN="ghp_xxx" \
  git push "https://x-access-token:${GIT_TOKEN}@github.com/owner/repo.git"
```

### 7.4 误提交 secret 怎么办
1. **立刻** Revoke:`Settings → Developer settings → PAT → Revoke`
2. 用 `git filter-repo` 清理历史:
   ```bash
   pip install git-filter-repo
   git filter-repo --path path/to/leaked --invert-paths
   git push --force
   ```
3. 通知 GitHub:`https://github.com/settings/security_advisories/new`

---

## 8. 监控 / Insights

### 8.1 关键指标(每周看一次)
- **Insights → Traffic**:star / fork / clone 趋势
- **Insights → Code frequency**:commit 频率
- **Insights → Dependency graph**:依赖更新提醒
- **Security → Dependabot alerts**:漏洞告警
- **Actions**:CI 失败率

### 8.2 告警配置
**Watch → Custom → ☑ 勾选**
- ☑ Releases
- ☑ Security alerts
- ☑ Discussions
- ☐ All Activity(太吵)

---

## 9. 常见操作剧本(Playbook)

### 9.1 发新版(管理员日常)

```bash
# 1. 拉最新 main
cd ~/Projects/aichat-hub
git checkout main
git pull origin main

# 2. bump version
vim CHANGELOG.md
# 在顶部加新条目

# 3. 跑测试
python3 -m pytest tests/ -v
# 必须 100% pass

# 4. build artifacts
bash packaging/build_deb.sh all
bash packaging/build_deb.sh arm64
bash packaging/build_deb.sh armhf
bash packaging/build_deb.sh amd64
bash packaging/build_macos.sh

# 5. commit + push
git add -A
git commit -m "Release v1.0.3"
git push origin main

# 6. 打 tag
git tag -a v1.0.3 -m "Release v1.0.3"
git push origin v1.0.3

# 7. GitHub Actions 自动建 release + 上传 artifacts
# 或手动:
gh release create v1.0.3 dist/*.deb dist/*.dmg --notes-file CHANGELOG.md
```

### 9.2 紧急回滚

```bash
# 找到出问题的 commit
git log --oneline -20

# 方式 A:revert(推荐,保留历史)
git revert <bad-commit-sha>
git push

# 方式 B:revert tag(发布事故)
git tag -d v1.0.2
git push origin :refs/tags/v1.0.2
# 然后在 GitHub 删 release + 重新打 tag 到上一个好的 commit
git tag -a v1.0.2 <good-commit-sha> -m "Revert v1.0.2"
git push origin v1.0.2
```

### 9.3 接受外部 PR

1. 仓库设置:**Allow fork PR** = ON
2. 收到 PR 后:
   - **Files changed** tab:仔细 review(就算小改动也看)
   - **Checks**:CI 全绿才能合
   - **Conversation**:解决所有评论
   - **Squash merge**(主策略),写清楚 commit message
3. 合并后:
   - 自动删 PR 分支(开启 "Automatically delete head branches")
   - 关闭相关 issue(用 `Closes #N`)
4. Contributor 致谢:
   - `README.md` 加 Contributors 段
   - `CHANGELOG.md` 致谢

### 9.4 处理 Issue
- **Triage**:
  - bug → label `bug`, 复现
  - feature → label `enhancement`, 转 PR 或 close
  - question → label `question`, 答
- **Stale bot**:`.github/workflows/stale.yml`(可选,30 天无活动自动 close)
- **Pinned issues**:把 `Welcome` `Roadmap` `Known Issues` 钉住

---

## 10. 项目专属配置

### 10.1 GitHub Pages(可选:部署文档)
- **Settings → Pages**
  - **Source**:`Deploy from a branch`
  - **Branch**:`gh-pages` / `root`
- push 到 `gh-pages` 自动部署
- 适合:`docs/` 目录 → `https://kzhou176-dot.github.io/ai-chat/`

### 10.2 Discussions
- **Settings → General → Features → ☑ Discussions**
- 类别建议:
  - 💡 Ideas(新点子)
  - 🙏 Q&A(使用问题)
  - 📣 Announcements(公告,只管理员可发)
  - 🐛 Bug Reports(虽然有 Issue,讨论版更轻量)
  - 🎓 Show and tell(用户分享用法)

### 10.3 Wiki(可选)
- 用法:写长文档(API 参考、教程)
- 维护成本高,推荐用 `docs/` + GitHub Pages

---

## 11. 故障排除

### 11.1 Push 被拒
```
! [remote rejected] main -> main (fetch first)
```
→ 远程有你没的 commit。`git pull --rebase` 然后再 push,**除非你确认要 force**。

### 11.2 Force push 安全
```bash
# 在 main 上 force 是危险的,先确认:
git log origin/main..HEAD   # 你要 push 的 commit
git log HEAD..origin/main   # 你会覆盖的 commit
# 确认无误,再 force:
git push --force-with-lease  # 比 --force 安全(如果别人 push 过会拒绝)
```

### 11.3 大文件
- `find . -size +50M` 找元凶
- 已经在历史里:`git filter-repo --path <file> --invert-paths` + force push
- 加到 `.gitignore`:`*.pdf`, `papers/pdfs/`

### 11.4 CI 跑不通
1. **Actions → 失败的 run → 详情**
2. 看具体 step 的 log
3. 90% 情况:依赖装不上 / Python 版本不对 / 路径写错
4. 本地重现:`act` 或直接装同版本 Python 跑

### 11.5 PR 冲突
```bash
git fetch origin
git checkout feature/my-branch
git rebase origin/main
# 解决冲突
git add .
git rebase --continue
git push --force
```

---

## 12. 每日 / 每周 / 每月检查清单

### 每日(5 min)
- [ ] 看 Issues 标签 `bug` 有无新的
- [ ] 看 PR 队列
- [ ] Actions 是否有失败

### 每周(30 min)
- [ ] Insights → Traffic
- [ ] Dependabot alerts
- [ ] 钉住的 issue 更新情况
- [ ] 回复老 issue(避免变成僵尸)

### 每月(2h)
- [ ] Review 贡献者 → 给权限
- [ ] 发版规划(下一版本定 features)
- [ ] 清理 stale 分支
- [ ] 备份重要 wiki 页面到 `docs/`

### 每季
- [ ] 大版本规划
- [ ] Token 轮换
- [ ] 安全审计(`git log --author` 异常作者 / `git fsck`)
- [ ] 重新 review 管理员手册(本文件)

---

## 附录 A:本项目仓库元数据

```yaml
name: ai-chat
owner: kzhou176-dot
visibility: public
default_branch: main
language: Python
license: MIT
size_kb: ~2700  # 2.7MB .git
files: 220
tests: 838
endpoints: 74
scripts: 26
docs: 28
papers: 60
release:
  latest: v1.0.2
  date: 2026-07-21
  artifacts:
    - aichat-hub_1.0.2_all.deb (305K)
    - aichat-hub_1.0.2_amd64.deb (305K)
    - aichat-hub_1.0.2_arm64.deb (305K)
    - aichat-hub_1.0.2_armhf.deb (305K)
    - aichat-hub-1.0.2-arm64.dmg (832K)
```

## 附录 B:GitHub CLI 速查

```bash
# 登录
gh auth login

# 仓库概览
gh repo view kzhou176-dot/ai-chat

# 列出 issue
gh issue list --repo kzhou176-dot/ai-chat
gh issue list --label bug --state open

# 创建 issue
gh issue create --title "..." --body "..." --label bug

# 创建 PR
gh pr create --title "..." --body "..." --base main

# 合并 PR
gh pr merge <num> --squash --delete-branch

# 创建 release
gh release create v1.0.3 dist/* --notes-file CHANGELOG.md

# 列出 workflow run
gh run list --limit 10
gh run watch <run-id>
```

## 附录 C:本手册变更日志

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0.2 | 2026-07-27 | 初版配套 v1.0.2 release |
