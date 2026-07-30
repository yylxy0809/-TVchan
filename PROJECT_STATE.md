# TVchan 项目状态总档案

**状态日期：2026-07-30**
**权威正式仓库：** `yylxy0809/-TVchan`
**正式主干：** `main@7cbf39b73a4ddcf39cca032bd904d33959ac593a`
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
5. 公开 market HTTP API、FastAPI 装配/readiness、TradingView datafeed 和写侧均未获当前实施授权；不要因离线测试通过而接线。
6. 任何 Python 工作前，第一条命令必须精确为 `uv python list`；随后显式使用选定解释器的绝对路径及其创建的隔离 venv。不得直接调用来源未确认的 `python`/`python3`。

## 3. 正式坐标、本地目录与工作树

| 项目 | 已证实坐标/用途 | 状态 |
|---|---|---|
| 远程仓库 | `https://github.com/yylxy0809/-TVchan` | 正式 |
| 正式主干 | `main@7cbf39b73a4ddcf39cca032bd904d33959ac593a` | PR #9 与状态档案 PR #10 均已合并 |
| 正式本地仓 | `D:/TVchan`，其当前 checkout 可能不在 `main`，所有主干事实以 `origin/main` 为准 | 只作仓库管理 |
| S1b 工作树 | `D:/TVchan-s1b-quality-calendar@58c798dd6a92e30e8c86f43afaa8fc96a0d7ad49` | 已由 PR #8 合入 main |
| 查询候选工作树 | `D:/TVchan-s1b-stockdb-query@f9d6c196fd7c8460d7074baa4ec3099f915ed63b` | PR #9 已合并；保留为历史证据 |
| 查询提交链 | `58c798d → d44bdbd → f9d6c19` | PR #9 head，已由 merge `1b3465c` 进入 main |
| 本档案工作树 | `D:/TVchan-project-state`，branch `docs/project-state-pr9` | 仅文档维护 |
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
| P5：计算与展示链 | `ChanEnginePort`/chan.py adapter、snapshot/publication、TradingView datafeed/overlay | **未开始** | 在 P4 有稳定读取语义前不得启动 |

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

## 7. 当前任务、依赖与优先级

| 优先级 | 任务 | 事实状态 | 依赖 / 下一步 |
|---|---|---|---|
| P0 | `T111` 状态总档案 | **进行中且常驻** | 本 PR 合并后持续更新本文件 |
| P0 | `T112` 离线查询竖切独立复核 | **已完成** | 已批准并由 PR #9 合入；保留其证据链 |
| P1 | real StockDB parity / provider capability | **未验证** | 需可用服务、公开 API、独立 live 证据 |
| P2 | API/readiness/TradingView/Chan | **未授权** | 不得因离线竖切已合入而推进 |

控制面提示：历史 `T108` 记录过 SSH/HTTPS 传输阻塞；但 S1b 的正式事实已由 PR #8 / `main@9c7e119` 覆盖。若任务板仍显示其外部等待，应由任务板 owner 做事实对齐，不能把该旧状态当作当前 S1b 发布授权或阻塞。PR #9 已证明显式代理 HTTPS 路径可以原样传输并合并已批准对象。

## 8. 已知问题与风险

1. **live `NOT_VERIFIED`**：离线 fixture、fake adapter 与 121-test 报告不能证明真实 StockDB 服务、网络、认证、分页或数据新鲜度。
2. **真实 StockDB parity 未完成**：需验证 public `get_data` 的 1d/30m/5m、复权值、DateRange/limit、not-found、timeout 和 provider protocol 错误；不得调用私有 helper。
3. **复权 reference 输入边界**：`QualityPolicy` 的 same-adjustment reference、`NONE` factor bar 和 calendar 均须由 application/adapter 明确提供；不得在 domain 内隐式获取或回写。
4. **API / TradingView 未接线**：没有公开 market endpoint、datafeed、overlay 或 browser acceptance；当前客户端不得读取本地候选。
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

## 常驻维护规则

`PROJECT_STATE.md` 是常驻文档，不随初版 PR 关闭。每次重要 PR 合并、固定候选形成或被拒绝、外部阻塞、阶段切换、live 证据变化或授权边界变化后，必须在同一事实变更的 docs-only 提交中更新本文件；不得把计划、猜测或未批准候选写成已完成。
