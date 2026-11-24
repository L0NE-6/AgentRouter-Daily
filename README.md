<div align="center">

<sub><strong>L0NE-6 · AGENTROUTER SIGNAL</strong></sub>

# AgentRouter Daily

**AgentRouter 每日额度 · 账号密码多账号 · 登录触发 · 严格 checked_in 回读**

> 当前版本：**v1.0.0**（2026-11-24） · 登录即触发额度，脚本只按布尔状态和回读结果判定

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

<img src="https://img.shields.io/badge/Features-Login%20Credit-6F42C1?style=for-the-badge" alt="Features" />
<a href="https://github.com/L0NE-6/AgentRouter-Daily/releases"><img src="https://img.shields.io/github/v/release/L0NE-6/AgentRouter-Daily?style=for-the-badge&label=Release&color=2ea44f&logo=github" alt="Release" /></a>
<a href="https://github.com/L0NE-6/AgentRouter-Daily/stargazers"><img src="https://img.shields.io/github/stars/L0NE-6/AgentRouter-Daily?style=for-the-badge&label=Stars&color=FFC75F&logo=github" alt="Stars" /></a>
<img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
<img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Qinglong-4EAA25?style=for-the-badge&logo=linux&logoColor=white" alt="Platform" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" alt="License" />

🔐 会话仅驻留内存 · ✅ 严格 checked_in · 👥 多账号隔离 · 🧾 JSONL · 🐧 青龙 · ☁️ GitHub Actions

[⚡ 30 秒速览](#quick-look) · [🔁 协议与回读](#protocol) · [🔐 凭据](#credentials) · [🐧 青龙](#qinglong) · [☁️ Actions](#actions) · [⌨️ CLI](#cli-json) · [✅ 成功判据](#success) · [✦ 星轨](#star-trail)

</div>

---

<a id="usage-policy"></a>
## 🚫 使用边界与禁止倒卖

> [!IMPORTANT]
> **官方版本永久免费。** 未经作者书面许可，禁止倒卖、付费包装、搬运引流、冒充作者，或使用作者身份与二维码制造官方授权假象。

本仓库、脚本、部署说明和 Release 下载保持免费公开。禁止将本项目或其轻度改名版本包装为付费资源、内部版、独家版、会员权益、收费课程、代部署服务或包更新服务；禁止搬运到其他账号、群组、频道、网盘、电商平台或付费社群进行涨粉、截流、倒卖和引流；禁止删除作者与版权信息后冒充原创。

完整规则见 [NOTICE.md](NOTICE.md)。第三方以“下载费 / 激活费 / 内部版 / 代部署 / 会员门槛”等名义收费，均与作者无关，请停止付款并保留证据。

---

<a id="quick-look"></a>
## ⚡ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **做什么** | 使用账号密码重新登录 AgentRouter，由登录动作触发当日额度。 |
| **输入** | `AGENTROUTER_ACCOUNTS`，或单账号 `AGENTROUTER_USERNAME` + `AGENTROUTER_PASSWORD`。 |
| **协议** | `POST /api/user/login`，会话来自 `Set-Cookie: session=...`。 |
| **回读** | 严格读取 `data.checked_in`；收到会话后再读取 `/api/user/self` 补充额度。 |
| **输出** | 每账号一条 JSON，最后一条汇总 JSON。 |
| **成功判据** | `success=true` 且 `data.checked_in=true` 记 `CLAIMED`；明确 `false` 记 `NO_NEW_GRANT`。 |

---

## 🧭 这是什么 / 覆盖范围

AgentRouter 的每日额度由登录动作触发，没有独立签到接口。脚本用账号密码登录，读取登录响应里的布尔字段 `data.checked_in`，并在拿到会话后调用 `/api/user/self` 补充 `quota`、`used_quota` 和总额度。

### 覆盖范围

- 账号密码登录与 `Set-Cookie: session` 会话接收。
- `data.checked_in=true/false` 严格判定，不接受字符串 `"true"` 或数字 `1`。
- `/api/user/self` 额度回读与状态冲突检测。
- 多账号逐项隔离、备注脱敏、JSONL 报告和 Actions 定时。
- 不提供 `--query`：登录本身可能产生真实副作用，不能伪装成只读查询。

---

<a id="protocol"></a>
## 🔁 协议与回读流程

### 请求链

```http
POST /api/user/login
Content-Type: application/json

{"username":"USERNAME","password":"PASSWORD"}

Set-Cookie: session=<session>
GET /api/user/self
```

### 关键字段

| 字段 | 类型 | 判定 |
| :--- | :--- | :--- |
| `success` | boolean | 登录是否被站点接受。 |
| `data.id` | number/string | 登录后的用户 ID。 |
| `data.checked_in` | boolean | `true` 表示本次登录新增当日额度；`false` 表示本次没有新增额度。 |
| `data.quota` | number | 剩余额度。 |
| `data.used_quota` | number | 已用额度。 |
| `Set-Cookie: session` | string | 登录会话；只在内存中使用，不写入日志。 |

`data.checked_in` 缺失、为字符串、为数字或为 `null` 时输出 `CHECKIN_UNCONFIRMED`。登录响应的 `data.checked_in` 与 `/api/user/self` 冲突时输出 `STATE_CONFLICT`。

---

<a id="credentials"></a>
## 🔐 凭据与环境变量

### 多账号

```text
备注|用户名|密码
```

密码可以包含 `|`，脚本按前两个分隔符切分。

### 环境变量

| 变量 | 必填 | 说明 |
| :--- | :---: | :--- |
| `AGENTROUTER_ACCOUNTS` | 二选一 | 多账号列表，每行 `备注\|用户名\|密码`。 |
| `AGENTROUTER_USERNAME` | 二选一 | 单账号用户名或邮箱。 |
| `AGENTROUTER_PASSWORD` | 二选一 | 单账号密码。 |
| `AGENTROUTER_BASE_URL` | 否 | 默认 `https://agentrouter.org`；可按实际站点设置。 |

---

## 💻 本地快速开始

### PowerShell

```powershell
python -m pip install -r requirements.txt
$env:AGENTROUTER_USERNAME = "user@example.com"
$env:AGENTROUTER_PASSWORD = "password"
python agentrouter_daily.py
```

### Bash

```bash
python -m pip install -r requirements.txt
export AGENTROUTER_USERNAME='user@example.com'
export AGENTROUTER_PASSWORD='password'
python agentrouter_daily.py
```

多账号可设置 `AGENTROUTER_ACCOUNTS`，只运行指定序号使用 `python agentrouter_daily.py --only 2`。

---

<a id="qinglong"></a>
## 🐧 青龙

1. 在青龙依赖管理中安装 `requests`，或执行 `pip3 install -r requirements.txt`。
2. 上传 `agentrouter_daily.py` 到脚本目录。
3. 在环境变量中配置 `AGENTROUTER_ACCOUNTS`，或 `AGENTROUTER_USERNAME` + `AGENTROUTER_PASSWORD`。
4. 新建定时任务，命令使用 `task agentrouter_daily.py`，不要直接写裸 `python`。
5. 建议北京时间：`17 8 * * *`。青龙按面板本地时间执行。

```bash
pip3 install -r requirements.txt
task agentrouter_daily.py
```

---

<a id="actions"></a>
## ☁️ GitHub Actions、Secrets 与定时

工作流：`.github/workflows/agentrouter.yml`。

| 事件 | 行为 |
| :--- | :--- |
| `push` 到 `main` | 单元测试、编译检查、Ruff。 |
| `schedule` | 先测试，再执行登录额度流程并上传 JSON 报告。 |
| `workflow_dispatch` | 手动执行同一套流程。 |

### Secrets 与变量

| 名称 | 类型 | 说明 |
| :--- | :--- | :--- |
| `AGENTROUTER_ACCOUNTS` | Secret | 多账号列表。 |
| `AGENTROUTER_USERNAME` | Secret | 单账号用户名或邮箱。 |
| `AGENTROUTER_PASSWORD` | Secret | 单账号密码。 |
| `AGENTROUTER_BASE_URL` | Repository variable | 可选站点根地址。 |

未配置凭据时，工作流输出 notice 并成功跳过在线执行。内置定时为 UTC `17 0 * * *`，对应北京时间约 08:17。GitHub schedule 可能延迟，不能保证准点。

---

<a id="cli-json"></a>
## ⌨️ CLI 与 JSON 输出

```powershell
python agentrouter_daily.py
python agentrouter_daily.py --only 2
```

当前脚本只有 `--only`，没有 `--query`。单账号 JSON 示例：

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
  "before_state": {"checked_in": false},
  "after_state": {"checked_in": true, "quota": 1000, "used_quota": 500}
}
```

| 字段 | 说明 |
| :--- | :--- |
| `result` / `ok` | 结果码与是否成功。 |
| `login_accepted` | 登录是否被接受。 |
| `session_received` | 是否收到会话，不输出会话值。 |
| `before_state` / `after_state` | 登录前后可见状态。 |
| `readback_error` | `/api/user/self` 回读失败原因，仅在存在时出现。 |

---

<a id="result-codes"></a>
## 🧾 结果码

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

---

<a id="success"></a>
## ✅ 成功判据

| 场景 | 必须满足 |
| :--- | :--- |
| 本次新增额度 | `success=true` 且 `data.checked_in=true`。 |
| 本次未新增额度 | `success=true` 且 `data.checked_in=false`，结果 `NO_NEW_GRANT`。 |
| 状态不可确认 | `checked_in` 缺失或不是 boolean，结果失败。 |
| 状态冲突 | `/api/user/self` 返回不同的 `checked_in`，结果失败。 |

HTTP 200、收到会话或拿到用户 ID 都不能单独证明额度已到账。

---

## 🧪 测试与静态检查

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check agentrouter_daily.py tests
```

离线测试使用 fake response 和 fake session，不连接真实账号。覆盖多账号密码含管道符、严格布尔判定、状态冲突、验证码阻断、错误脱敏和配置错误。

---

## 🧱 设计原则

- **登录就是动作**：不把可能触发额度的登录伪装成只读查询。
- **布尔严格**：`true`、`"true"`、`1` 三者不混用。
- **回读补证**：登录响应决定主结果，`/api/user/self` 只补充额度和冲突检测。
- **凭据不落盘**：会话仅在进程内存中使用。
- **账号隔离**：单个账号失败不阻断其他账号。

---

## 🔒 隐私

仓库不包含账号、密码、会话、手机号、邮箱、运行日志或真实响应。`agentrouter-report.json` 与 `agentrouter-report.jsonl` 已由 `.gitignore` 排除，不能提交。

---

## 📁 目录结构

```text
AgentRouter-Daily/
├── .github/workflows/agentrouter.yml
├── assets/
│   ├── donate-alipay.jpg
│   └── donate-wechat.png
├── docs/
│   ├── README.en.md
│   ├── README.zh-Hant.md
│   ├── README.ja.md
│   ├── README.ko.md
│   └── README.pt-BR.md
├── tests/test_agentrouter_daily.py
├── CHANGELOG.md
├── LICENSE
├── NOTICE.md
├── THIRD_PARTY_NOTICES.md
├── agentrouter_daily.py
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

## 📦 版本与发布

- 当前清单版本：`v1.0.0`，日期 `2026-11-24`。
- 脚本版本与 `agentrouter_daily.py` 内的 `VERSION` 保持一致。
- 更新记录见 [CHANGELOG.md](CHANGELOG.md)，下载入口见 [Releases](https://github.com/L0NE-6/AgentRouter-Daily/releases)。
- Release 徽标由 GitHub 实时生成；如果页面尚未创建对应 Release，以 `CHANGELOG.md` 和仓库提交为准。

---

## ⚠️ 免责声明

本项目用于个人学习与个人自动化。AgentRouter 的活动规则、接口、奖励、风控策略和账号资格由服务方决定。使用前请确认对应服务条款，并自行承担接口变化、账号限制和网络环境带来的风险。

---

## ☕ 支持与投喂

脚本完全免费，赞赏纯自愿，不影响任何功能，也不影响 Issue 响应。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝收款码" />
</p>
<p align="center"><sub>💚 微信支付（左） &nbsp;|&nbsp; 💙 支付宝（右，支持信用卡 / 花呗）</sub></p>

> 收款码仅用于向作者自愿赞赏。任何第三方以代下载、代部署、内部资源或会员群为由收费，均与作者无关。

---

## 💬 反馈与贡献

- 提交 [Issue](https://github.com/L0NE-6/AgentRouter-Daily/issues) 时附运行日志、脱敏后的错误字段和复现步骤。
- 发起 [Pull Request](https://github.com/L0NE-6/AgentRouter-Daily/pulls) 时保持单文件运行、离线测试和凭据脱敏约束。
- 不要在任何 Issue、PR、截图或日志中粘贴真实 Token、Cookie、密码、UID、手机号或邮箱。

---

<a id="star-trail"></a>
## ✦ Star History / 星轨

<a href="https://star-history.com/#L0NE-6/AgentRouter-Daily&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=L0NE-6/AgentRouter-Daily&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=L0NE-6/AgentRouter-Daily&type=Date" />
    <img alt="AgentRouter-Daily Star History" src="https://api.star-history.com/svg?repos=L0NE-6/AgentRouter-Daily&type=Date" />
  </picture>
</a>

<div align="center">
  <sub>L0NE-6 · DAILY SIGNAL &nbsp;|&nbsp; 点个 <b>Star</b>，让下一轮自动化有迹可循</sub>
</div>
