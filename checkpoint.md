# TVchan 项目停机检查点（2026-07-30）

> 状态：**用户主动暂停，禁止继续执行**  
> 生成时间：2026-07-30 07:46（UTC+8，约等于 2026-07-29 23:46Z）  
> 正式仓库：`yylxy0809/-TVchan`  
> 检查点分支：`checkpoint/pause-20260729`  
> CCCC group：`g_c6e3c870b7c1`  
> 最后稳定控制面：`ctxv:745`  
> 正式远端主干：`origin/main@0760cfa383cbe799ae72a3c0eaee4b9484da6ebc`  
> 固定 S1b 候选：`f670493ce6ca4befafc0c382e8496f1f355f7b2a`  

**本文件完整取代 2026-07-29 的旧 checkpoint 内容。旧文件中 `main@771e5aa`、T034 未发布等陈述已经过时，不得作为恢复依据。**

---

## 1. 本次暂停指令

用户已明确要求：

- 暂停分配新任务；
- 汇总所有代理进展并写入 checkpoint；
- 用户将停机一段时间；
- 在用户再次明确授权恢复前，不继续开发、复核、候选验收、发布、PR、合并或 S2 工作。

Foreman 已向全组发送停机检查点指令：

- 禁止创建、领取或启动新任务；
- 已有工作停在最近的安全边界；
- 不为赶停机而补跑命令或强行形成 APPROVE；
- 牛马4若未形成完整 T087 结论，应保留为 PARTIAL；
- 任务板管理与追踪只记录技术结论，不代作技术判断；
- 不创建后继候选验收卡。

随后 CCCC web-model connector 已停止，因此未能收齐停机指令后的全员最终回复。本文件只使用停机前已确认的控制面、Git/worktree 事实、冻结制品和已收到的代理报告，不补造任何结论。

---

## 2. 恢复时的事实优先级

恢复后按以下顺序认定事实：

1. Git 远端引用、精确 commit/tree SHA 与 clean 状态；
2. 冻结制品的绝对路径、SHA-256 与 manifest；
3. CCCC 最后稳定控制面 `ctxv:745`；
4. 停机前已收到的代理二元结论；
5. 历史 checkpoint、旧 agent_state 或旧任务 notes 仅作背景，不得覆盖以上事实。

任何对象身份不一致，必须停止并重新规划；不得自行 rebase、cherry-pick、改写、替换工具或“按惯例”补全。

---

## 3. Git、分支与 worktree 现实

### 3.1 正式远端

- 仓库：`git@github.com:yylxy0809/-TVchan.git`
- `origin/main`：`0760cfa383cbe799ae72a3c0eaee4b9484da6ebc`
- 提交说明：`Merge pull request #7 from yylxy0809/phase1/s1a-market-contract`
- 其父提交：
  - `771e5aa4c2fdc19ce828846a50c801bd044bb92e`
  - `9006710d7ed7620e2efb44d244b24d585c41c8c5`

### 3.2 重要本地现实差异

`D:\TVchan` 当前**不是**正式 main 工作树：

- 当前分支：`audit/legacy-tv-mapping-v1`
- HEAD：`6585c9bd995b0e466ca1cf2edbe82ad3c6c2e30a`
- 状态：clean

本地 `main` 分支为：

- `eab60e0e68406de516affb9d4b773d802e244fb2`
- 相对 `origin/main`：behind 13、ahead 0

因此恢复时不得在 `D:\TVchan` 直接假定自己位于正式主干，也不得直接 reset、checkout 或改写；先只读核验并明确选择正确 worktree。

### 3.3 当前 worktree 清单

| 路径 | 分支/状态 | HEAD | 备注 |
|---|---|---|---|
| `D:\TVchan` | `audit/legacy-tv-mapping-v1` | `6585c9b` | clean，非正式 main |
| `D:\TVchan-audit` | `audit/legacy-mapping-v2` | `9d5977f` | 历史迁移审计 |
| `D:\TVchan-checkpoint` | `checkpoint/pause-20260729` | 本文件更新前 `ded7ff5` | 专用 checkpoint worktree |
| `D:\TVchan-phase0-gate` | `phase0/dependency-gate` | `044d78f` | Phase 0 gate 载体 |
| `D:\TVchan-gate` | `wave1/gate-hardening` | `eb0bb83` | gate hardening 历史工作树 |
| `D:\TVchan-s1a-contract` | `phase1/s1a-market-contract` | `9006710` | clean，已通过 PR #7 合入 main |
| `D:\TVchan-s1b-quality-calendar` | `phase1/s1b-quality-calendar` | `f670493` | clean，固定候选，未 push |
| `D:\TVchan-wave0` | `wave0/bootstrap` | `506c7d9` | 历史工作树 |
| `D:\TVchan-wave1-contract` | `wave1/contract-admission` | `5f476cb` | 历史契约载体 |

另外存在两个 `C:\tmp` detached worktree，分别固定在 `ad493af` 与 `9006710`，仅作历史验收取证。

### 3.4 PROJECT.md 提示的真实含义

CCCC bootstrap 一直提示：

```text
PROJECT.md missing (expected at D:\TV\PROJECT.md)
```

这是因为 CCCC active scope 仍指向旧项目 `D:\TV`。实际新项目 `D:\TVchan\PROJECT.md` 已存在。恢复时应优先把 CCCC 项目 scope 对齐到 `D:\TVchan`，不要在旧项目中补建或覆盖 PROJECT.md。

---

## 4. 项目阶段进展

### 4.1 Phase 0：已完成

- PR #5 已合入，merge commit：`6e347379f0251d1db16f6dd2bc12d1d4d52c2b73`
- PR #6 已合入，merge commit：`771e5aa4c2fdc19ce828846a50c801bd044bb92e`
- 依赖边界 gate 已完成独立黑盒验收并进入主干。

### 4.2 S1a：已完成并合入 main

最终 S1a 载体：

- 分支：`phase1/s1a-market-contract`
- 最终 head：`9006710d7ed7620e2efb44d244b24d585c41c8c5`
- PR #7：已 MERGED
- merge commit：`0760cfa383cbe799ae72a3c0eaee4b9484da6ebc`
- main CI：SUCCESS

S1a 仅批准市场领域词汇、端口和 Quality provenance DTO，不自动批准 S1b、S2、provider I/O、QueryService、实时采集、Chan、Snapshot、API 或 TradingView。

### 4.3 S1b：实现已固定，最终独立准入未完成

固定候选：

- worktree：`D:\TVchan-s1b-quality-calendar`
- branch：`phase1/s1b-quality-calendar`
- HEAD：`f670493ce6ca4befafc0c382e8496f1f355f7b2a`
- tree：`5cd91483aa6ffa70d6cc4d99b0789226baf98f68`
- 状态：clean
- 未 push

提交链：

```text
0760cfa
  -> d4d4bd9ce616944b0b1dfe843b06a2a7c4e4ce3e  Add S1b quality policy
  -> af14b199e3b35f2f9cb357b07804060b61cfe41f  Add static trading calendar
  -> f670493ce6ca4befafc0c382e8496f1f355f7b2a  Document S1b quality semantics
```

实现者冻结前验证：

- pytest：72 passed；
- ruff check：PASS；
- ruff format check：PASS；
- mypy：PASS；
- dependency gate：PASS；
- diff-check：PASS。

这些结果是实现者交付证据，不替代最终独立候选验收。

### 4.4 S1b 验收链进展

1. 原 scope scanner 出现字符串误报；
2. 结构化 scope v3 已重建并由牛马4独立 APPROVE；
3. scope v3 已实际扫描固定候选并 PASS；
4. 原 Oracle 在执行 43 个断言前因越权导入失败：
   - 错误地从 `tvchan.domain.market` facade 导入 `SHANGHAI`；
   - 0/43 断言执行；
5. T082 归因结论：`B — ORACLE_UNAUTHORIZED_IMPORT`；
6. T083 生成唯一权威 Oracle v2，只修改 SHANGHAI import owner；
7. T088 由牛马7完成制品可靠性核验，结论 `ARTIFACT_RELIABLE`；
8. T087 已激活，由牛马4执行候选盲技术复核；停机时尚未收到最终 APPROVE/REJECT；
9. 牛马6尚未执行固定候选最终验收；
10. S1b 尚未获得最终准入，不得 push、PR 或据此启动 S2。

---

## 5. 冻结制品与唯一身份

### 5.1 Scope v3 包

根目录：`C:/tmp/tvchan-s1b-scope-v2-t070/`

| 制品 | SHA-256 |
|---|---|
| `scan_s1b_scope_v2.py` | `D11CBECC7172A3522A1168C46669BDF3E5726AA278E677041792FDF07318A572` |
| runner | `91D839786E304C00AA19835141F8A38998BCEDCBD9744B7E0A7CFC1FD1BB2849` |
| fixtures | `66D7A69195EC898B0DE3E0D7E0E103F89749D1C3EC434CF758C92AEBB8180798` |
| `replay_v3.py` | `CD979EA97557B1F7ADCEB5F2C9B7F3ABDEF6819EEB1C0E683EDF05E2C8DB3A6D` |
| `manifest-v3.json` | `28B063545B5D7DD99D3C1B2AFD9AB8AAB246DC18CB351B017895295CF29741F0` |

T079 独立结论：APPROVE，仅批准 scope gate 工具，不批准候选。

### 5.2 Oracle v2 唯一权威包

| 对象 | 路径 | SHA-256 |
|---|---|---|
| 原 Oracle | `C:/tmp/tvchan-s1b-oracle-t061/frozen/oracle_s1b.py` | `2819349DA58FE87A2EE433A6DA8750B395D2B3C685D89AF5FDE92F45A2E882A5` |
| Oracle v2 | `C:/tmp/tvchan-s1b-oracle-t083/frozen/oracle_s1b_v2.py` | `968A9FF0505884894DCD76AE3736D872065E44253D1260F3F3CD6D1DA7B4095C` |
| fixture | `C:/tmp/tvchan-s1b-oracle-t083/frozen/s1b_fixture.json` | `16B86FF84CC53D2E5AF7272A26D0BCCD5D8682ADC673CB052FBB848BCB2D6A83` |
| manifest v2 | `C:/tmp/tvchan-s1b-oracle-t083/frozen/manifest-v2.json` | `C668ED68C0A1658C1C5AB5B834DE4DFF4FD184416B07EDFE3DCF91048911CCAF` |

T083 允许的唯一语义差异：

```python
# 删除
from tvchan.domain.market import SHANGHAI

# 新增
from tvchan.domain.market.model import SHANGHAI
```

43 个 assert 调用及 29+14 测试上下文、CLI 与 fixture 读取语义必须保持不变。

### 5.3 T088 制品可靠性结论

牛马7已核验：

- 四路径可达；
- 四个 SHA-256 在运行前后稳定；
- manifest 记录一致；
- 解释器：`Python 3.12.7`；
- `py_compile` exit 0；
- 零候选参数 CLI exit 1，stderr 仅 usage；
- 在 candidate import 前退出；
- 未读取候选、仓库、Git 或 scope v3；
- 结论：`ARTIFACT_RELIABLE`。

该结论只证明固定包可靠，不证明 Oracle 语义正确，也不证明候选通过。

### 5.4 明确排除 T086

T086 是牛马1并行构建的历史 Oracle v2 制品，路径与 hash 不同。它不得进入 T087 或后继候选验收。唯一权威对象是 T083 包。

---

## 6. 停机时任务板状态

最后稳定控制面 `ctxv:745`：

- planned：T080；
- active：T077、T087；
- done：T088、T089、T090，以及此前已闭环任务；
- 历史 archived 卡保留原停止与继承记录。

### T087：独立复核 S1b Oracle v2 冻结包

- status：`active`
- waiting_on：`none`
- 行政 owner：`任务板管理与追踪`
- 唯一技术 reviewer：`牛马4`
- C001：`in_progress`
- C002/C003/C004：pending
- 候选盲边界仍有效
- 停机前未收到完整 APPROVE/REJECT

T087 已收窄：候选盲阶段只允许 hash、manifest、文本/AST diff、43=29+14 结构、py_compile 与零参数 usage 停止点；带候选启动、导入与断言必须留到后继候选验收。

### T077：常驻任务板治理

- status：`active`
- 只负责生命周期、证据、等待和 closeout；
- 不作技术实现或技术验收；
- 停机时仍需清理少量过期 open loop，例如“等待 Foreman 绑定/激活 T087”的旧字段。

### T080：常驻独立技术审查

- status：`planned`
- 角色规程未完整关闭；
- 当前 T087 的实际技术 reviewer 仍是牛马4；
- 停机期间不得自行启动。

### T088 / T089 / T090

- T088：done，牛马7，`ARTIFACT_RELIABLE`；
- T089：done，牛马5，契约/ADR岗位规程就绪；
- T090：done，牛马6，候选验收执行规程就绪。

---

## 7. 当前团队全部代理进展

### 7.1 chatgpt_web — Foreman

已完成：

- 总架构、范围、阶段门禁与任务授权；
- Phase 0、S1a 的治理与准入链；
- S1b 契约、实现、scope、Oracle 归因和分权验收链编排；
- 新增并冻结牛马5/6/7岗位边界；
- 激活 T087，同时保持行政 owner 与技术 reviewer 分离；
- 发出全组停机检查点指令；
- 更新本 checkpoint。

停机时未完成：

- T087最终技术结论；
- 牛马6候选最终验收；
- S1b发布/PR/合并；
- S2正式授权。

未修改业务代码、候选、Oracle、scope 或 Git 历史。

### 7.2 codex_cli — Release / PR / CI / Git 集成管理员

已完成：

- T082 只读归因，确认旧 Oracle 越权导入；
- 历史 S1a 发布、PR 与主干合并链；
- 当前无 active task。

停机状态：只读待命。

恢复后不得自行验收候选；只有在牛马6最终 APPROVE且 Foreman另行授权后，才可执行发布、PR、CI 与 Git 集成。

### 7.3 grok_build — 历史独立审查/备援

已完成：

- 旧项目接管简报与显隐/空白图审查；
- 历史控制面治理与专项审计；
- 当前无 active task。

停机前 runtime 曾显示 `stuck / pty_no_prompt_stuck`，但无执行任务，不构成当前技术阻塞。恢复后仅在明确授权下工作。

### 7.4 牛马1 — 验收工具与反例集构建

已完成：

- scope scanner v2、确定性修复、Windows-safe replay v3；
- T076冻结包；
- 历史并行 T086 Oracle 制品。

当前无 active task。

注意：T086不得进入权威验收链。牛马1不负责候选最终验收。

### 7.5 牛马2 — Oracle 构建与版本维护

已完成：

- T083唯一权威 Oracle v2 冻结包；
- 原 Oracle、fixture、manifest 与 scope v3均保持不变；
- 当前无 active task。

牛马2不得验收自己维护的 Oracle；恢复后只有 T087精确 REJECT 指向 T083缺陷时，才可接收最小修复任务。

### 7.6 牛马3 — 代码实现负责人

已完成：

- T065 S1b QualityPolicy 与 StaticTradingCalendar实现；
- 固定候选 `f670493`；
- 冻结前工程检查全绿；
- 当前无 active task。

停机期间不得修改固定候选。只有最终候选验收精确 REJECT 指向实现缺陷时，才可接收新修复任务。

### 7.7 牛马4 — 独立技术复核 / 红队

已完成：

- 多轮 scope 工具独立复核；
- T087前置判断：候选盲与“带候选启动”冲突，要求拆分工具健康与候选执行健康；
- 促成 T087收窄。

停机时状态：

- T087 active；
- runtime 最后显示 working；
- agent_state仍残留“等待绑定”的过时描述，但控制面已确认 T087 active；
- 未收到最终 APPROVE/REJECT或PARTIAL报告；
- 不得假定其已经完成，也不得直接重跑。

恢复后第一件事是恢复其最后消息/执行证据，确认停机前是否已经形成完整结论。

### 7.8 任务板管理与追踪 — 控制面治理

已完成：

- T077常驻治理；
- T087行政 owner；
- 记录T088可靠性前置、候选盲边界和牛马4技术 reviewer身份。

停机时：

- T077 active；
- T087 active/C001 in_progress；
- 不得代替牛马4形成技术结论；
- 不得自行创建后继候选验收卡；
- 少量过期 open loop需在恢复后清理。

### 7.9 独立技术审查 — 常驻角色草案

- T080 planned；
- 角色目标为固定对象的独立 APPROVE/REJECT/NOT_READY；
- 当前没有获授权执行对象；
- 不得与牛马4的T087并行重复审查。

### 7.10 牛马5 — 契约与 ADR 负责人

T089已完成并签收：

- 最低输入材料清单；
- 公共API、exports、DTO、签名、错误、状态、文件范围、测试矩阵模板；
- READY/NOT_READY二元门；
- ADR不可变历史与 supersedes 规则；
- 跨岗位交接接口；
- 禁止自批、自实现、自建最终Oracle。

当前只读待命。S2未授权，不得提前起草或落码S2业务契约。

### 7.11 牛马6 — 候选验收执行官

T090已完成并签收：

- 前置缺失即 NOT_STARTED；
- 固定对象不一致即 REJECT；
- 顺序固定、首次失败立即停止；
- 必须记录命令、cwd、exit、输出、断言、停止点和未运行项；
- 结论仅绑定“候选×工具链×命令单”；
- 禁止修改候选、工具、标准或为失败修复。

当前只读待命，明确被 T087未APPROVE及无新验收卡阻塞。未读取或运行 `f670493`。

### 7.12 牛马7 — 环境与制品可靠性负责人

T088已完成并关闭：

- 路径/hash/manifest/CPython/py_compile/零参数CLI核验；
- 结论 `ARTIFACT_RELIABLE`；
- 未作语义或候选裁决；
- 当前只读待命。

恢复后只报告制品或环境身份漂移，不得改业务语义或给技术 APPROVE。

### 7.13 历史角色说明

历史角色 `claude`、`规划`、`执行者`、`执行者2`、`帮手` 的相关任务已经闭环，其有效结果已经体现在 `origin/main@0760cfa` 和控制面历史中。它们不属于本次停机时的12人当前运行团队，不应被自动重新激活。

---

## 8. 当前非业务基础设施问题

### 8.1 NotebookLM / Group Space

停机前连续出现：

- `space_provider_upstream_error`；
- `space_provider_auth_invalid`；
- 提示需要执行 `notebooklm login` 重新认证。

该问题只影响 Group Space / NotebookLM 镜像同步，不影响 Git、任务板、冻结制品或 S1b验收事实。恢复后可选修复，不是恢复T087的前置条件。

### 8.2 CCCC connector

用户停机后，web-model connector 返回：

```text
connector_actor_stopped
```

因此：

- 未能收齐停机指令后的全员最终回复；
- 未能在 CCCC 内把所有 agent_state统一改为停机状态；
- 本 checkpoint 已改用停机前 `ctxv:745` 与Git事实收口。

恢复时必须重新 bootstrap，而不能假定当前内存状态仍在。

---

## 9. 恢复顺序（必须严格执行）

只有用户明确说“恢复项目”后，才允许执行：

1. 恢复 CCCC 连接，确认 group `g_c6e3c870b7c1`；
2. 将 active scope 对齐新项目 `D:\TVchan`，不要继续以旧 `D:\TV` 为项目根；
3. 调用 `cccc_bootstrap`，读取本 checkpoint 和停机期间新增消息；
4. `git fetch --prune origin`；
5. 核验 `origin/main` 是否仍为 `0760cfa383cbe799ae72a3c0eaee4b9484da6ebc`；
   - 若变化，停止并重新规划；
   - 不得自行 rebase/cherry-pick/reset；
6. 核验固定候选：
   - HEAD=`f670493ce6ca4befafc0c382e8496f1f355f7b2a`
   - tree=`5cd91483aa6ffa70d6cc4d99b0789226baf98f68`
   - parent chain=`0760cfa -> d4d4bd9 -> af14b19 -> f670493`
   - worktree clean；
7. 核验 scope v3 与 T083 Oracle v2全部路径/hash/manifest；
8. 恢复牛马4停机前最后证据：
   - 若已有完整T087结论，只接收原结论，不重跑；
   - 若为PARTIAL，继续同一T087、同一T083包、同一候选盲边界；
   - 若无证据，重新开始T087但不得触候选；
9. T087若REJECT：只精确退回T083缺陷给牛马2，不改候选；
10. T087若APPROVE：由Foreman创建**唯一**后继候选最终验收卡并指派牛马6；不得指派Oracle作者；
11. 牛马6验收顺序固定：
    1. immutable preflight；
    2. scope v3；
    3. Oracle v2/Harness；
    4. pytest；
    5. ruff check；
    6. ruff format check；
    7. mypy；
    8. dependency gate；
    9. diff-check；
    10. 人工七文件范围核验；
    - 首次失败立即停止，后续全部标记未运行；
12. 只有牛马6对固定候选与固定工具组合APPROVE后，Foreman才能另行授权codex_cli发布/PR；
13. PR仍需独立准入与Foreman合并授权；
14. S2必须另外获得用户/Foreman明确授权；S1b完成不自动启动S2。

---

## 10. 暂停期间禁止事项

- 不创建或启动任何新任务；
- 不读取、运行或修改固定候选，除非恢复后牛马6获得正式验收卡；
- 不修改 `f670493`、其父链或worktree；
- 不修改T083 Oracle v2、fixture、manifest或scope v3；
- 不使用T086替代T083；
- 不把T088 `ARTIFACT_RELIABLE`解释为技术或候选批准；
- 不以mock证明候选导出面；
- 不在 `D:\TVchan` 当前审计分支上直接开发；
- 不使用本地过时 `main@eab60e0`作为正式基线；
- 不push S1b分支，不创建或合并S1b PR；
- 不启动S2、StockDB provider、实时采集、Chan、Snapshot、API或TradingView新实现；
- 不向StockDB原始表写入或回写qfq数据；
- 不清理、覆盖或重建现有冻结目录和历史manifest；
- 不把旧checkpoint内容当作当前事实。

---

## 11. 最小恢复摘要

当前项目已完成 Phase 0、S1a，并在 `origin/main@0760cfa` 建立正式基线。S1b实现候选 `f670493` 已固定、clean、未push；scope v3已独立批准并扫描候选PASS；旧Oracle失败被归因为Oracle越权导入；唯一权威T083 Oracle v2已冻结，T088已证明制品可靠。停机时唯一技术主门是T087：牛马4正在候选盲复核T083包，但最终结论尚未收到。恢复后先找回T087最后证据；只有T087 APPROVE后，才能由牛马6按固定顺序执行候选最终验收。S2仍未授权。
