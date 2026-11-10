# CONTRIBUTING — Collaboration rules（两人协作规则）

> 本项目由 **Gav**（Gavin Li）和 **Aya**（艾亚）共同完成。本文件规定两人在 GitHub 上怎么署名、开分支、提交和合并，保证每一处改动都能看出是谁做的、谁审过。
>
> AI 助手（Codex / Claude）也遵守本文件；`AGENTS.md` §6 引用了这里的规则。

---

## 1. Members（成员）

| Tag | Name | GitHub | 用于 commit / PR | 用于 branch |
|---|---|---|---|---|
| `Gav` | Gavin Li | `gavin0829afg` | `[Gav]` | `gav/` |
| `Aya` | 艾亚 | `ayaw888` | `[Aya]` | `aya/` |

---

## 2. 署名规则（最重要）

### 2.1 Commit message

格式：

```
[Tag] <module>: <what changed>
```

例子：

```
[Gav] costs: add per-side spread model
[Aya] masking: rebase prices to decision-date close
[Aya] docs: fill week-1 go/no-go table
```

- **谁负责这次改动，就写谁的 Tag。** 用 AI 写的代码也一样：Aya 让 Codex 写的提交，前缀就是 `[Aya]`。
- **有 AI 参与时，在 commit message 末尾加一行说明是哪个 AI**，例如：
  ```
  AI-assisted: Codex
  ```
  或 Claude 自动加的 `Co-Authored-By: Claude ...`。这样以后可以看出哪些代码经过人工审查、哪些是 AI 写的。

### 2.2 Branch name

格式：

```
<tag>/<short-topic>
```

例子：`gav/pilot-script`、`aya/masking-spec`、`aya/fix-leak-check`

- 全小写，单词之间用 `-` 连接。
- 一个分支只做一件事，做完合并后删除。

### 2.3 Pull Request

- **PR 标题和 commit 一样，以 `[Tag]` 开头**，例如 `[Aya] masking: implement price and date masking`。
- 合并时选 **Squash and merge**：main 上每个 PR 只留一个提交，提交信息就是 PR 标题，前缀自然保留下来。

### 2.4 Git 身份

每个人在**自己电脑上的这个仓库里**设置一次（不要改别人的配置）：

```powershell
git config user.name "艾亚的名字"
git config user.email "<GitHub noreply 邮箱>"
```

noreply 邮箱在 GitHub → Settings → Emails 里找，格式是 `数字+用户名@users.noreply.github.com`。用它可以避免在公开仓库里暴露真实邮箱。

---

## 3. 工作流程（每次改动都按这个顺序）

```powershell
# 1. 先同步最新的 main
git switch main
git pull

# 2. 开自己的分支
git switch -c aya/masking-spec

# 3. 改代码、提交（可以多次）
git add <files>
git commit -m "[Aya] masking: ..."

# 4. 推送分支
git push -u origin aya/masking-spec

# 5. 开 PR，请对方审查
gh pr create --title "[Aya] masking: ..." --body "做了什么 / 怎么测的 / 需要重点看哪里"
```

然后：

1. **对方审查**：在 PR 页面看改动、留评论，没问题就 Approve。
2. **高风险模块**（`AGENTS.md` §5：masking、leak_check、stats、costs、run_grid、评级映射）**合并前还要让 Claude 审查一遍**，审查结论以 PR 评论的形式贴出（流程见 §4.3）。
3. **合并**：Squash and merge，然后删除分支。
4. **不直接往 main 推送。** 包括文档改动在内，都走 PR，这样对方一定能看到。

---

## 4. AI 工具怎么参与 PR

### 4.1 每个人用什么工具

| Person | Tools | 角色 |
|---|---|---|
| Gav | Claude（设计、审查）+ Codex（实现） | Claude 起草任务和审查 PR，Codex 写代码并开 PR |
| Aya | Codex（实现，也可用来自查） | Codex 写代码并开 PR；高风险模块的 Claude 审查由 Gav 协助完成 |

**AI 能做和不能做的事：**

| 可以 | 不可以 |
|---|---|
| 开分支、提交、推送**自己的**分支 | 推送到 `main` |
| 开 PR（包括 draft PR） | **自行合并 PR**（只有 PR 作者明确让它合并某个 PR 时才可以） |
| 在 PR 下发表评论 | 代替人点 Approve |
| 在自己的分支上追加提交来修改 | 改别人的分支；审查开始后 force push |

### 4.2 任务从哪里来：用 Issue 传递

Aya 没有 Claude，所以 Claude 起草的任务说明不能只留在 Gav 的聊天记录里。**所有任务都写成 GitHub Issue**：

- Issue 标题：`[Task] <module>: <要做什么>`，指派（assign）给负责的人。
- Issue 正文：任务说明（目标、要改哪些文件、验收标准）。Gav 可以让 Claude 直接起草并创建 Issue。
- 负责人把 Issue 链接或编号交给自己的 Codex：`读 Issue #12，按 AGENTS.md 完成它`。Codex 可以用 `gh issue view 12` 读取。

### 4.3 两种 PR 流程

**流程 A：Gav 的任务（Claude + Codex）**

```
Claude 起草任务 → 创建 Issue（assign 给 Gav）
   ↓
Codex：同步 main → 开分支 gav/<topic> → 实现 + 测试 → [Gav] 提交 → 推送 → 开 PR（Closes #Issue）
   ↓
Claude 审查 PR（gh pr diff），以评论形式发表 "Claude review"
   ↓
Codex 按审查意见在同一分支追加提交
   ↓
Aya 审查并 Approve → Gav 点 Squash and merge
```

**流程 B：Aya 的任务（Codex）**

```
Issue（assign 给 Aya）
   ↓
Codex：同步 main → 开分支 aya/<topic> → 实现 + 测试 → [Aya] 提交 → 推送 → 开 PR（Closes #Issue）
   ↓
Gav 审查；如果涉及高风险模块，Gav 让 Claude 审查这个 PR，Claude 以评论形式发表 "Claude review (via Gav)"
   ↓
Aya 的 Codex 按意见在同一分支追加提交
   ↓
Gav Approve → Aya 点 Squash and merge
```

**规则：PR 由作者本人合并，但必须先拿到对方的 Approve。** GitHub 不允许给自己的 PR 点 Approve，所以 Claude 用 Gav 的账号发的审查只能是"评论"，正式的 Approve 必须来自另一个人。

### 4.4 PR 的格式

- **标题：** 和 commit 一样，例如 `[Aya] masking: implement price rebasing`。
- **正文：** 仓库里的 `.github/pull_request_template.md` 会自动填进 PR 正文，内容就是 Codex 的汇报格式（`AGENTS.md` §8），外加 Issue 编号和高风险模块勾选项。用 `gh pr create` 时要加 `--body-file` 或按模板手动填写。
- **没做完先开 draft：** `gh pr create --draft`，做完后 `gh pr ready`。
- **AI 发表的评论开头要写明来源**，例如 `**Claude review (via Gav)**` 或 `**Codex (Aya)**`，避免和人写的评论混在一起。

### 4.5 如果 Codex 不能联网或没有 `gh`

Codex 的沙箱有时会限制网络。这种情况下 Codex 做到本地提交为止，然后在汇报里写明"未推送"，由人来运行：

```powershell
git push -u origin <branch>
gh pr create --title "<同 commit 标题>" --body-file <汇报文件>
```

---

## 5. 分工与避免冲突

- **开工前先认领任务**：在 GitHub 上开一个 Issue（或在已有 Issue 上 assign 给自己），写明要改哪些文件。两个人（以及各自的 AI）不要同时改同一个文件。
- **设计决定要两个人都同意**：实验网格、指标、阈值、成本假设等预注册设定（`AGENTS.md` 规则 4），修改前在 Issue 或 PR 里讨论，确定后写进 `INSTRUCTIONS.md` §11 Decision Log，注明是谁提出的、谁同意的。
- **AI 汇报**：Codex 的汇报（`AGENTS.md` §8 格式）就是 PR 正文（见 §4.4），对方和 Claude 都能看到。

---

## 6. 实验运行与结果

- **谁运行、在哪台机器上运行都要记录。** 两个人的电脑硬件不同，同一个 seed 在不同 GPU 上的输出也可能有细微差别。每条运行记录都要带 `operator`（`gav` / `aya`）和 `machine` 字段（见 `INSTRUCTIONS.md` §5.3）。
- **同一个实验尽量在同一台机器上跑完。** 如果要两台机器分摊，按"股票"或"周"切分，并在 Decision Log 里记录怎么分的。
- **原始结果不进 git**（`results/raw/` 已被忽略）。需要共享时，用两人约定的网盘传输，`results/tables/` 下的汇总表和 `RUN_INFO.md` 可以提交。
- 每台机器各自在 `RUN_INFO.md` 里记录一份环境信息（Ollama 版本、模型 digest、GPU 型号）。

---

## 7. 不能提交的内容

见 `AGENTS.md` 规则 8：`.env`、API key、token、Bloomberg 数据、大型原始日志。提交前运行 `git status` 检查一遍。
