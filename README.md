<div align="center">

<sub><strong>L0NE-6 · AGENTROUTER SIGNAL</strong></sub>

# AgentRouter Daily

**AgentRouter 每日额度 · 账号密码多账号 · 登录触发 · 严格 checked_in 回读**

> 当前版本：**v1.0.0**（2026-11-24） · 单文件运行 · 没有独立签到接口 · 不假报奖励

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

<img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Qinglong-4EAA25?style=for-the-badge" />
<img src="https://img.shields.io/badge/Deploy-GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />

</div>

## 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| 做什么 | 用账号密码重新登录 AgentRouter，由登录动作触发当日额度。 |
| 请求 | `POST /api/user/login`，JSON body 为 `username` / `password`。 |
| 会话 | 登录响应通过 `Set-Cookie: session=...` 下发会话，不是 JSON `token` 字段。 |
| 状态 | 严格读取 `data.checked_in`，并用登录后的 `/api/user/self` 补充额度回读。 |
| 独立签到 | 没有。脚本不调用 `/api/user/checkin`。 |
| 成功 | 只有 `checked_in=true` 才记为 `CLAIMED`。 |

## 登录即签到

```text
POST /api/user/login
  body: {"username":"...","password":"..."}
  |
  +-- HTTP / success 失败 -> AUTH_REJECTED / HTTP_ERROR / BLOCKED
  |
  +-- data.checked_in=true
  |     -> 本次登录新增当日额度 -> CLAIMED
  |
  +-- data.checked_in=false
  |     -> 登录成功，但本次没有新增额度 -> NO_NEW_GRANT
  |
  +-- checked_in 缺失或不是 boolean
        -> CHECKIN_UNCONFIRMED
```

固定接口语义：

| 字段 | 类型 | 语义 |
| :--- | :--- | :--- |
| `success` | boolean | 登录是否被站点接受。 |
| `data.id` | number/string | 站点用户 ID，可用于登录后的状态回读。 |
| `data.checked_in` | boolean | `true` 表示本次登录新增当日额度；`false` 表示没有新增额度。 |
| `data.quota` | number | 剩余额度。 |
| `data.used_quota` | number | 已用额度。 |
| `Set-Cookie: session` | string | 登录会话；脚本只保存在内存中，不输出。 |

`data.checked_in` 缺失、为字符串 `"true"`、为 `1` 或 `null` 时都不算成功。
登录响应没有可依赖的 JSON `token` 字段；会话来自 `Set-Cookie: session`。

## 前后状态

账号密码本身不能在“登录前”做一次无副作用的账户状态读取，因为登录就是触发额度动作。脚本明确记录这一点：

| 场景 | `before_state.checked_in` | `after_state.checked_in` | 结果 |
| :--- | :---: | :---: | :--- |
| `checked_in=true` | `false`，由服务端“本次新增额度”语义推出 | `true` | `CLAIMED` |
| `checked_in=false` | `null`，没有安全的登录前读取 | `false` | `NO_NEW_GRANT` |
| 字段缺失/类型错误 | `null` | `null` | `CHECKIN_UNCONFIRMED` |

当登录响应带有 `session` 与用户 ID 时，脚本会再调用一次
`GET /api/user/self`，补充 `quota` / `used_quota`。该回读被验证码或 WAF
拦截时，会在 `readback_error` 中记录，不会把登录响应里的 `checked_in`
伪造成余额变化。

## 凭据

### 多账号

`AGENTROUTER_ACCOUNTS` 每行一个账号：

```text
备注|用户名|密码
```

密码可以包含 `|`，脚本按前两个分隔符切分。

示例：

```text
账号一|user-one|password-one
账号二|user@example.com|password:with:colons
```

### 单账号

```powershell
$env:AGENTROUTER_USERNAME = "user@example.com"
$env:AGENTROUTER_PASSWORD = "password"
```

| 变量 | 必填 | 说明 |
| :--- | :---: | :--- |
| `AGENTROUTER_ACCOUNTS` | 二选一 | 多账号列表。 |
| `AGENTROUTER_USERNAME` | 二选一 | 单账号用户名或邮箱。 |
| `AGENTROUTER_PASSWORD` | 二选一 | 单账号密码。 |
| `AGENTROUTER_BASE_URL` | 否 | 默认 `https://agentrouter.org`。国内站可设为 `https://ps.air-outer.com`。 |

脚本输出只显示备注，不显示用户名、密码或 `session`。

## 本地运行

```powershell
python -m pip install -r requirements.txt

$env:AGENTROUTER_USERNAME = "user@example.com"
$env:AGENTROUTER_PASSWORD = "password"
python agentrouter_daily.py
```

多账号：

```powershell
$env:AGENTROUTER_ACCOUNTS = @"
账号一|user-one|password-one
账号二|user@example.com|password-two
"@
python agentrouter_daily.py
```

只运行第二个账号：

```powershell
python agentrouter_daily.py --only 2
```

本脚本没有 `--query`。该站点没有独立 `/checkin`，而登录本身可能触发额度；把登录包装成“只查询”会产生真实副作用。

## 青龙面板

| 步骤 | 操作 |
| :---: | :--- |
| 1 | 在依赖管理安装 `requests`。 |
| 2 | 上传 `agentrouter_daily.py`。 |
| 3 | 环境变量新增 `AGENTROUTER_ACCOUNTS` 或单账号两变量。 |
| 4 | 新建定时任务，命令填 `task agentrouter_daily.py`。 |
| 5 | 建议北京时间每天 `08:17` 运行一次。 |

## GitHub Actions

仓库内置 [`.github/workflows/agentrouter.yml`](.github/workflows/agentrouter.yml)。

| 事件 | 行为 |
| :--- | :--- |
| push 到 `main` | 运行单元测试、编译检查和 Ruff。 |
| schedule | 先测试，再执行登录签到并上传 JSON 报告。 |
| workflow_dispatch | 手动执行同一套流程。 |

### Secrets

| Secret | 必填 | 值 |
| :--- | :---: | :--- |
| `AGENTROUTER_ACCOUNTS` | 二选一 | 多账号列表。 |
| `AGENTROUTER_USERNAME` | 二选一 | 单账号用户名或邮箱。 |
| `AGENTROUTER_PASSWORD` | 二选一 | 单账号密码。 |

可选仓库变量 `AGENTROUTER_BASE_URL` 用于切换站点基址。未配置凭据时，定时任务输出明确的跳过通知并成功结束。

## 输出字段

单账号结果示例：

```json
{
  "account": "account_1",
  "provider": "agentrouter",
  "result": "CLAIMED",
  "ok": true,
  "login_accepted": true,
  "session_received": true,
  "claimed": true,
  "checked_in": true,
  "before_state": {
    "checked_in": false,
    "source": "implied_by_data.checked_in_true"
  },
  "after_state": {
    "checked_in": true,
    "quota": 1000,
    "used_quota": 500,
    "balance_total": 1500,
    "source": "login_response+user_self"
  }
}
```

| 字段 | 说明 |
| :--- | :--- |
| `login_accepted` | 登录接口是否被站点接受。 |
| `session_received` | 是否从 `Set-Cookie` 收到 `session`，不输出其值。 |
| `before_state` | 登录前状态；无安全前置读取时明确为 `null`。 |
| `after_state` | 登录响应和可选 `/api/user/self` 的后置状态。 |
| `readback_error` | 可选状态回读失败原因。 |

## 结果码

| 结果码 | 成功 | 含义 |
| :--- | :---: | :--- |
| `CLAIMED` | 是 | 登录成功且 `data.checked_in=true`。 |
| `NO_NEW_GRANT` | 是 | 登录成功且站点明确返回 `data.checked_in=false`。 |
| `CHECKIN_UNCONFIRMED` | 否 | 登录成功，但签到标记缺失或不是 boolean。 |
| `STATE_CONFLICT` | 否 | 登录响应与 `/api/user/self` 的 `checked_in` 冲突。 |
| `AUTH_REJECTED` | 否 | 用户名、密码或会话被拒绝。 |
| `BLOCKED` | 否 | 返回 HTML 验证页而不是 JSON。 |
| `RATE_LIMITED` | 否 | HTTP 429。 |
| `BUSINESS_ERROR` | 否 | 站点业务错误。 |
| `HTTP_ERROR` | 否 | 非 2xx HTTP 错误。 |
| `NETWORK_ERROR` | 否 | 网络异常或超时。 |
| `INVALID_JSON` | 否 | 返回内容不是 JSON。 |
| `INVALID_RESPONSE` | 否 | JSON 结构错误。 |
| `CONFIG_ERROR` | 否 | 环境变量或基址配置错误。 |

## 成功判据

本项目不把“登录请求返回 200”直接当成签到成功。

| 场景 | 必须满足 |
| :--- | :--- |
| 本次新增额度 | `success=true` 且 `data.checked_in=true` |
| 本次未新增额度 | `success=true` 且 `data.checked_in=false`，输出 `NO_NEW_GRANT` |
| 标记不可确认 | `checked_in` 缺失或不是 boolean，输出失败 |
| 状态冲突 | `/api/user/self` 返回不同 `checked_in` 时输出失败 |

`NO_NEW_GRANT` 只表示站点明确没有报告本次新增额度，不代表已经确认此前发过奖励。

## 测试

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check agentrouter_daily.py tests
```

离线测试全部使用 fake response 和 fake session，不连接真实账号。

## 隐私

本仓库不包含账号、密码、`session`、手机号、邮箱、运行日志或真实响应。
不要把 `agentrouter-report.json`、`agentrouter-report.jsonl`、密码、会话或截图提交到仓库。

## 支持

脚本免费公开。如果它确实帮你省了时间，欢迎自愿赞赏。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝收款码" />
</p>

> 收款码仅用于向作者自愿赞赏。任何第三方以代下载、代部署、内部版或会员群为由收费，均与作者无关。

## 免责声明

本项目用于个人学习和合法的个人自动化。AgentRouter 的活动规则、接口、每日额度、验证码和账号资格由服务方决定；使用前请确认对应服务条款，并自行承担接口变化和账号风险。

## 文件

```text
agentrouter_daily.py
tests/test_agentrouter_daily.py
.github/workflows/agentrouter.yml
docs/README.en.md
docs/README.zh-Hant.md
docs/README.ja.md
docs/README.ko.md
docs/README.pt-BR.md
LICENSE
NOTICE.md
THIRD_PARTY_NOTICES.md
```
