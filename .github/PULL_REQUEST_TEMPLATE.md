## 变更类型
- [ ] Bug fix(非破坏性)
- [ ] New feature(非破坏性)
- [ ] Breaking change(会影响现有功能)
- [ ] Documentation only
- [ ] Refactor(无功能变化)

## 变更摘要
<!-- 简述这个 PR 改了什么 -->

## 关联 Issue
<!-- "Closes #123" 或 "Refs #456" -->

## 测试
- [ ] 本地跑通 `python3 -m pytest tests/ -v`(全 838+ tests 通过)
- [ ] 新功能有对应测试(`tests/test_<N>_<name>.py`)
- [ ] 没破坏现有功能
- [ ] 跑过 `python3 scripts/benchmark.py run`(如涉及 endpoint)
- [ ] 跑过 `python3 scripts/e2e_demo.py all`(如涉及用户旅程)

## 改动文件
<!-- 简要列出关键文件变化 -->
- 
- 
- 

## 截图(如有 UI 变化)

## Checklist
- [ ] 代码风格一致(`python3 -m compileall scripts/ tests/` 通过)
- [ ] 更新了 CHANGELOG.md(如果是新功能)
- [ ] 更新了 README.md / docs/(如果改了用户接口)
- [ ] commit message 清晰(参考 git log)
- [ ] 关联的 issue 已加 `pr: in-review` 标签
