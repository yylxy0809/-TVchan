# TVchan 项目状态总档案

**状态日期：2026-07-30**
**权威正式仓库：** `yylxy0809/-TVchan`
**正式主干：** `main@18c57b573cf16b00725edf220e6c241f1e449063`
**用途：** 新窗口、新 Agent 和审查者的唯一项目接管入口。它只记录已证实事实；架构细节仍以 `PROJECT.md`、`docs/WAVE1_MARKET_CONTRACT.md` 与 ADR 为准。

## 读法与状态标记

- **已完成**：已进入正式 `main` 或已由固定验收链批准。
- **进行中**：有明确负责人和固定对象，但尚未进入 `main`。
- **未验证**：不得以测试绿灯或样例替代真实外部能力。
- **禁止**：未经新的明确授权不得实施、发布或合并。

## 1. 项目目标与总体架构

TVchan 重构目标是把旧项目中可验证的行情、缠论和展示能力迁入可维护的新边界，而不是整体复制 `D:/TV`。最终高层数据路径为：

```text
free-stockdb → MarketDataGateway / StockDB Adapter → chan.py Adapter
            → FastAPI read model → TradingView read-only presentation
```

依赖方向固定为：

```text
Presentation / API → Application → Domain
Application → Ports ← Adapters / Infrastructure
Bootstrap 仅负责装配
```

Domain 和 Application 不得导入 FastAPI、TradingView、StockDB SDK/HTTP 客户端、数据库或 adapter 实现。`chan.py` 是未来计算内核，只能经 `ChanEnginePort`/adapter 接入，禁止重写或直接耦合。

## 2. 用户硬约束与当前禁区

1. `D:/TVchan` 是唯一正式目标仓库；`D:/TV` 仅为旧行为、fixture 和迁移证据，默认只读。
2. 保持提交小、范围可审计；不得在工作树混入无关改动、改写已验收历史或用“等价代码”替代已批准 SHA。
3. Wave 1 仅允许 market contract、只读 adapter、quality/calendar、health/readiness 与后续明确授权的查询链；禁止提前引入 Chan、snapshot、writer、realtime、lifecycle、strategy、backtest 或 TradingView 实现。
4. 禁止使用 StockDB 私有 SDK helper（包括 `_apply_fq_in_memory`、`_merge_*`）；仅可包装公开、可测试的能力。原始数据不得回写。
5. 已合入的范围仅为固定 TradingView market datafeed/widget 前端竖切；专有 `charting_library` 仍保持仓外，overlay、sidecar、live provider、写侧、release 与浏览器端验收均未获新授权。
6. 任何 Python 工作前，第一条命令必须精确为 `uv python list`；随后显式使用选定解释器的绝对路径及其创建的隔离 venv。不得直接调用来源未确认的 `python`/`python3`。

## 3. 正式坐标、本地目录与工作树

| 项目 | 已证实坐标/用途 | 状态 |
|---|---|---|
| 远程仓库 | `https://github.com/yylxy0809/-TVchan` | 正式 |
| 正式主干 | `main@18c57b573cf16b00725edf220e6c241f1e449063` | PR #14 已以 merge commit 合并；两父为 `7ba98f3` 与 `bc085e6` |
| 正式本地仓 | `D:/TVchan`，其当前 checkout 可能不在 `main`，所有主干事实以 `origin/main` 为准 | 只作仓库管理 |
| S1b 工作树 | `D:/TVchan-s1b-quality-calendar@58c798dd6a92e30e8c86f43afaa8fc96a0d7ad49` | 已由 PR #8 合入 main |
| 查询候选工作树 | `D:/TVchan-s1b-stockdb-query@f9d6c196fd7c8460d7074baa4ec3099f915ed63b` | PR #9 已合并；保留为历史证据 |
| 查询提交链 | `58c798d → d44bdbd → f9d6c19` | PR #9 head，已由 merge `1b3465c` 进入 main |
| 本档案工作树 | `D:/TVchan-project-state-pr14`，branch `docs/project-state-pr14-merge` | 本轮合并后 docs-only 维护；旧 `D:/TVchan-project-state@40c9a8f` 仅本地草稿，不推送 |
| 旧仓库 | `D:/TV` / `yylxy0809/tv` | 非正式、只读参考 |

不要将旧 Wave 0、S1a、gate、checkpoint 或 audit worktree 当成当前实现分支；它们是历史证据，不是继续开发的起点。

## 4. 角色与责任矩阵

| 角色 | 责任 | 不得承担 |
|---|---|---|
| Foreman (`chatgpt_web`) | 范围冻结、架构裁决、任务编排、最终阶段放行 | 代替实现或独立验收 |
| Codex CLI | Release/PR/CI/Git 集成、只读归因、`PROJECT_STATE.md` 常驻维护 | 自批自己实现或绕过固定对象 |
| 任务板管理与追踪 | 生命周期、证据治理、控制面一致性 | 技术实现或技术裁决 |
| 牛马1 | 验收工具与反例集 | 最终候选验收 |
| 牛马2 | Oracle 构建与版本维护 | 审批自身 Oracle |
| 牛马3 | 实现 | 审批自身候选 |
| 牛马4 | 独立技术审查 / 红队 | 实现被审对象 |
| 牛马5 | 契约、ADR 与边界裁决材料 | 实现或自批最终 Oracle |
| 牛马6 | 固定候选最终验收执行 | 修改候选或工具 |
| Grok | 专项研究、原型和风险复核 | 替代正式集成或 live 证明 |

## 5. 全盘路线：P0–P5 与 S1 切片

| 阶段 | 目标 | 当前状态 | 进入条件 / 禁区 |
|---|---|---|---|
| P0：工程与治理基线 | 包、CI、pytest/ruff/mypy、依赖闸门、发布治理 | **已完成** | 不含业务迁移 |
| P1 / S1a：market contract core | Canonical `Symbol`/`Timeframe`/`Bar`、ports、typed errors、DTO | **已完成**，PR #7 已进入 `main@0760cfa` | 不含 QueryService、adapter、API、Chan |
| P2 / S1b：quality 与静态日历 | `QualityPolicy`、`StaticTradingCalendarAdapter`、ADR-005 | **已完成**，PR #8 已进入 `main@9c7e119` | 不含 StockDB/HTTP、API、Chan |
| P3：离线 historical query 竖切 | 只读 StockDB adapter、`MarketDataQueryService`、offline fixture/fake | **已完成首个离线竖切**，PR #9 已进入 main | 禁止以离线 fixture 声称 live parity；真实 provider parity 仍未验证 |
| P4：受控读取交付 | 经新授权后接入 readiness/bootstrap、公开只读 market API、真实 provider parity | **未开始** | 不得提前接 FastAPI/TradingView |
| P5：计算与展示链 | `ChanEnginePort`/chan.py adapter、snapshot/publication、TradingView datafeed/overlay | **仅 datafeed/widget 竖切已完成** | PR #14 仅合入固定前端 datafeed；overlay、sidecar、live/write、release 与其余 P5 均未授权 |

实时、lifecycle、replay、strategy、backtest 和 writer 属于更后阶段；除非新的 ADR 与 Foreman 明确授权，否则均为禁止项。

## 6. 已完成与进行中的工程事实

### S1a：已完成

- PR #7 `feat: establish S1a market contract core` 已以 merge commit 进入 `main@0760cfa383cbe799ae72a3c0eaee4b9484da6ebc`。
- 固定了 A 股 canonical symbol、timeframe、adjustment、timezone-aware half-open `DateRange`、Decimal `Bar`、provenance、quality DTO、`MarketDataGateway` 和独立 `TradingCalendarPort`。

### S1b：已完成

- PR #8 `S1b: add quality policy and static trading calendar` 已合并：head `58c798dd6a92e30e8c86f43afaa8fc96a0d7ad49`，base `0760cfa...`，merge commit `9c7e11979f6e7b5c13414baa5900c4ec7b188182`。
- 完整范围严格为 7 个文件：market export、`QualityPolicy`、market infrastructure export、`StaticTradingCalendarAdapter`、两组测试、`ADR-MARKET-005`。
- 固定验收链通过 scope v3、Oracle v3、`pytest`（73 passed）、ruff、format、mypy、dependency gate 与 diff-check；该批准不扩展到 query、StockDB、API、Chan 或 live provider。

### 查询竖切：已完成（仅离线能力）

- `d44bdbd47dda994ed4438d808cae417c887d79ce`：从已合并 S1b head 引入只读 StockDB adapter（来源为已批准的离线原型）。
- `f9d6c196fd7c8460d7074baa4ec3099f915ed63b`：加入 `MarketDataQueryService` 离线 historical-query vertical。
- 固定链 `58c798d → d44bdbd → f9d6c19` 已由 T112 批准、PR #9 合并：base `9c7e119...`、head `f9d6c19...`、merge commit `1b3465c02ed1be4c069b7f184a01b8c6af495b7c`。其本地验收报告为 **121 tests**；该事实仅覆盖离线能力。
- 其文件范围包括 application market query、StockDB public-client adapter/mapping/normalization/settings、fake client、offline fixture 与测试；不代表 real StockDB 已可用。

### TradingView datafeed/widget：已完成固定前端竖切（非发布授权）

- PR #14 `feat(frontend): add TradingView market datafeed` 已于 2026-07-30 以 merge commit `18c57b573cf16b00725edf220e6c241f1e449063` 合入 `main`。
- 合并双父精确为旧 main `7ba98f31d9e8d6dc6264c770df163b872f6a6619` 与已批准候选 `bc085e66839df6e3f3bc937370b329da6a2d694c`；后者 tree 为 `c52760b72df584d443935544898825ebc1a81323`，直接父为 `8860f3a01bcff17f20116efebf9acacbfc770660`，且为新 main 祖先。
- 累计范围精确为 11 个 `frontend/` 文件：前 10 个业务文件由 T159 固定审查，`bc085e6` 仅追加 `frontend/.gitignore`（`node_modules/`）。T219=`ARTIFACT_RELIABLE`、T220/T221=`APPROVE`；T221 仅绑定 T155 Oracle v2 与 T157 批准；T244 对冻结 PR #14 给出 `APPROVE MERGE`。
- 合并前 PR #14 的两条 `verify` 均成功且 `CLEAN/MERGEABLE`；合并后 main CI run `30572702429` 为 `success`。这不授权 release，也不授权 `charting_library` 入库、overlay、sidecar、live provider、写侧或其他 P5 工作。

## 7. 当前任务、依赖与优先级

| 优先级 | 任务 | 事实状态 | 依赖 / 下一步 |
|---|---|---|---|
| P0 | `T111` 状态总档案 | **进行中且常驻** | PR #14 已合并；本轮从新 main 重建 docs-only 状态档案 |
| P0 | `T112` 离线查询竖切独立复核 | **已完成** | 已批准并由 PR #9 合入；保留其证据链 |
| P1 | real StockDB parity / provider capability | **未验证** | 需可用服务、公开 API、独立 live 证据 |
| P2 | API/readiness/TradingView/Chan | **未授权** | 不得因离线竖切已合入而推进 |

### 当前受控工作链（任务板当前快照）

| 工作链 | 任务 | 当前事实 | 允许的下一步 / 禁区 |
|---|---|---|---|
| P3 纯计算候选 | `T177` | **进行中**：在固定 `main@7ba98f3` 与已审输入上实现最小纯计算纵向切片 | 不读取 Oracle、不 push/PR；完成后才能冻结单父候选供非构建者验收 |
| P3 Oracle 可靠性 | `T188` | **进行中**：仅独立核验 T187 的 Oracle v4 制品可靠性 | 只能输出 `ORACLE_ARTIFACT_RELIABLE` 或 `NOT_READY`；不批准语义、实现、候选、发布 |
| Parquet v2 | `T245` | **已完成**：内部合成向量 v2 已冻结，`SYNTHETIC_PARQUET_V2_READY_FOR_INDEPENDENT_REVIEW` | 不含用户数据、网盘、正式 adapter、正式仓、写库或发布 |
| Parquet v2 独立复核 | `T248` | **计划中**：等待对 T245 固定 v2 制品的独立复核 | 仅验证 B05 零 I/O 反证及完整向量重放；不批准实现或发布 |
| 主图 v0 契约机械冻结 | `T246` | **进行中**：机械冻结唯一内容寻址契约对象 | 不改语义、不读候选/Oracle/代码、不实施 overlay |
| 主图 v0 契约独立复核 | `T241` | **计划中**：仅等待 T246 固定路径、manifest、SHA256SUMS 与字节数 | 不读实现代码或专有库；APPROVE 仅允许未来版本化实现规划输入 |
| 状态档案 | `T111` / `T249` | **进行中**：本轮以 `18c57b5` 合并事实重建 docs-only 记录 | 不复用或推送旧本地 `40c9a8f`；本轮 PR 未经审查不得合并 |

### 历史组织快照（非当前调度）

| 组别 | 任务 | 当前事实 | 依赖 / 禁止事项 |
|---|---|---|---|
| A：市场只读 API 与展示 | `T114` | **进行中**：冻结 P5 市场 API 与 TradingView 契约 | 契约先于实现；不得自批最终 Oracle |
| A：市场只读 API 与展示 | `T115` | **进行中、等待 T114**：实现 P5 市场只读 FastAPI 接口 | 只可按 T114 READY 契约实施 |
| A：市场只读 API 与展示 | datafeed 竖切 | **已完成**：PR #14 已合入 main | 仅固定 datafeed/widget；不授权 overlay、sidecar、live/write、release 或专有库入仓 |
| B：chan.py 纯计算接入 | `T116` | **进行中**：只读现实映射 | 先确定最小计算切片，不得将旧项目耦合迁入 |
| B：chan.py 纯计算接入 | `T118` | **已完成**：P3 纯计算验收工具骨架 | 候选盲、未冻结具体 Chan 算法期望 |
| B：chan.py 纯计算接入 | `T120` | **进行中**：P3 黄金样本输入包 | 冻结来源、manifest 和未决语义，不能替代实现验收 |
| 跨线支持 | `T121` | **进行中**：双线环境与制品可靠性基线 | 只建可重放环境证据，不裁决业务语义 |
| 跨线支持 | `T122` | **进行中**：双线最终验收执行单 | 必须在固定对象形成后运行；首失败即停 |
| 跨线支持 | `T123` | **计划中**：双线独立技术审查值守 | 不能审查自身实现或自身 Oracle |
| 治理 / 状态 | `T077` 与 `T111` | **常驻** | 前者维护任务治理；后者维护本档案；均不代替技术实现 |

组织原则（用户最新管理要求）：多数开发代理不得长期空闲；管理者只负责规划、分配、裁决和验收，不亲自实施业务代码。每个交付仍须由互不自证的实现、工具/Oracle、独立审查与发布责任链构成。

### 历史业务工作基线例外（已因 PR #14 失效）

历史上，`main@25cf091620f77a6432b8865013b91325f59d16d7` 相对 `413c1e132f70714830ff9a129679965c117799ea` 仅有文档差异，因此曾允许固定父仍为 `413c1e1` 的业务候选继续完成验收。这不是一般性的“忽略主干”许可。

- 已复核 `git diff --name-only 413c1e1..25cf0916` 仅输出 `PROJECT_STATE.md`；对 `backend frontend vendor src application domain infrastructure` 的目录限定 diff 为空。
- PR #14 已将 11 个 `frontend/` 业务文件合入 main，故该 docs-only 例外现已失效：任何新业务候选必须以当前 main 为准，或先由 Foreman 重新裁决其集成基线。历史候选与证据仍保留，但不得据此继续开发。
- 发布或整合时仍须从固定业务候选向最新 `main` 建立普通 PR，并重新核验 base/head、范围、CI 与 mergeability；不得借此例外改写候选历史。
- **失效条件：** 一旦 `413c1e1..当前 main` 出现任何 `backend/`、`frontend/`、`vendor/`、`domain/`、`application/` 或 `infrastructure/` 的业务差异，本例外立即失效，必须暂停并由 Foreman 重新裁决基线与是否重建。

控制面提示：历史 `T108` 记录过 SSH/HTTPS 传输阻塞；但 S1b 的正式事实已由 PR #8 / `main@9c7e119` 覆盖。若任务板仍显示其外部等待，应由任务板 owner 做事实对齐，不能把该旧状态当作当前 S1b 发布授权或阻塞。PR #9 已证明显式代理 HTTPS 路径可以原样传输并合并已批准对象。

## 8. 已知问题与风险

1. **live `NOT_VERIFIED`**：离线 fixture、fake adapter 与 121-test 报告不能证明真实 StockDB 服务、网络、认证、分页或数据新鲜度。
2. **真实 StockDB parity 未完成**：需验证 public `get_data` 的 1d/30m/5m、复权值、DateRange/limit、not-found、timeout 和 provider protocol 错误；不得调用私有 helper。
3. **复权 reference 输入边界**：`QualityPolicy` 的 same-adjustment reference、`NONE` factor bar 和 calendar 均须由 application/adapter 明确提供；不得在 domain 内隐式获取或回写。
4. **接线边界仍有限**：PR #14 已合入固定 datafeed/widget 前端竖切，但没有公开 market endpoint、专有 `charting_library`、overlay、sidecar、live provider、写侧、release 或 browser acceptance；不得把该竖切解释为全量 TradingView 交付。
5. **旧仓库不是部署目标**：`D:/TV` 可作只读行为比较，不能复制 backend、迁移私有 SDK 路径或在其中实施新架构。

## 9. Git 网络故障与恢复

曾出现 Git SSH/默认 HTTPS 无响应。已证实的恢复方式是显式绕开全局 URL 改写并走系统代理：

```powershell
$env:http_proxy = 'http://127.0.0.1:7897'
$env:https_proxy = 'http://127.0.0.1:7897'
$env:GIT_TERMINAL_PROMPT = '0'
$env:GCM_INTERACTIVE = 'Never'
git -C D:\TVchan fetch --prune https://github.com:443/yylxy0809/-TVchan.git `
  '+refs/heads/main:refs/remotes/origin/main'
```

原因：系统代理是 `127.0.0.1:7897`，且全局 `insteadOf` 会将常规 HTTPS URL 改写为 SSH。显式 `https://github.com:443/...` 与显式代理避免该改写。发布前仍须先只读 `ls-remote`/`push --dry-run` 验证认证；只能普通 non-force push 已批准 SHA，绝不能用 GitHub API/connector 重建提交、补丁、cherry-pick 或产生新 SHA。

## 10. Python 固定规则

任何 Python 工作的第一条命令必须是：

```powershell
uv python list
```

当前 Wave 1 基准是 CPython 3.12；已安装基础解释器为 `C:\ProgramData\anaconda3\python.exe`（3.12.7）。最终验证不得直接使用 Anaconda base：先由该绝对路径创建项目隔离 venv，再显式调用 venv 的 `python.exe` 安装依赖和运行 pytest、ruff、mypy、脚本。每份证据必须记录 `uv python list`、base 路径与版本、venv 路径与版本。3.11/3.10 绿灯不能作为合并证据。

## 11. 新窗口接管步骤

1. 阅读本文件、`PROJECT.md`、`docs/WAVE1_MARKET_CONTRACT.md`，并按工作内容阅读相关 ADR。
2. 先核验 `origin/main` 是否仍等于本文件所载 SHA；若已变化，记录新 merge commit、父链、PR 与 CI，再更新本文件，不要依据旧工作树继续开发。
3. 用 `git worktree list --porcelain` 和 `git status --porcelain` 核对目标工作树；不要切换、污染或重用历史 worktree。
4. 查看任务板的 active/planned 卡及 `waiting_on`，以固定对象和独立审批为授权边界；历史聊天不是执行授权。
5. 若要运行 Python，先执行精确 `uv python list`，再创建/使用 CPython 3.12 隔离 venv。
6. 对 provider/live、PR 或合并动作，先重新核验远程 head/base/checks/mergeability；任一漂移即停。

## 12. 变更日志

| 日期 | 事实 |
|---|---|
| 2026-07-30 | 初版建立：记录 `main@9c7e119`、S1a/S1b 完成、S1b PR #8、离线查询候选链 `58c798d→d44bdbd→f9d6c19`、live 未验证风险、Git 代理恢复方法与 Python 固定规则。 |
| 2026-07-30 | 维护更新：PR #9 已将离线 StockDB adapter 与 `MarketDataQueryService` 链（head `f9d6c19`）以 merge `1b3465c` 合入；随后状态档案初版 PR #10 以 merge `7cbf39b` 合入。正式 main 更新为 `7cbf39b`；离线竖切完成不等同于 live parity。 |
| 2026-07-30 | 维护更新：状态档案 PR #11 以 merge `413c1e1` 合入，确认 PR #9 的离线查询竖切为已完成事实。随后建立 A 组（T114/T115/T117）、B 组（T116/T118/T120）及跨线支持（T121/T122/T123）；T077 与 T111 为常驻治理卡。 |
| 2026-07-30 | 基线裁决：`main@25cf091` 相对 `413c1e1` 仅有 `PROJECT_STATE.md` 的 docs 差异，业务目录 diff 为空。已在 `413c1e1` 建立的业务 worktree/仓库外制品无需因 docs-only 合并重建；六个指定业务目录任一出现差异即失效并重新裁决。 |
| 2026-07-30 | PR #14 已将固定 TradingView market datafeed/widget 候选以 merge `18c57b5` 合入 main；双父为 `7ba98f3` 与 `bc085e6`，main CI run `30572702429` 成功。累计11个 frontend 文件已按 T159/T218/T219/T220/T221/T155/T157 分层验收；无 release、overlay、sidecar、live/write 或专有库入仓授权。该业务变更使历史 `413c1e1` docs-only 基线例外失效。 |

## 常驻维护规则

`PROJECT_STATE.md` 是常驻文档，不随初版 PR 关闭。每次重要 PR 合并、固定候选形成或被拒绝、外部阻塞、阶段切换、live 证据变化或授权边界变化后，必须在同一事实变更的 docs-only 提交中更新本文件；不得把计划、猜测或未批准候选写成已完成。
