# AgentRouter Daily

[简体中文](../README.md) · **English** · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

AgentRouter grants the daily credit through login. This runner signs in with
the username and password, then reports the strict `data.checked_in` state.

## Contract

```text
POST /api/user/login
body: {"username":"...","password":"..."}
```

The session is returned as `Set-Cookie: session=...`; the reviewed source does
not consume a JSON `token` field from the login body.

| `data.checked_in` | Meaning | Result |
| :--- | :--- | :--- |
| `true` | This login added the day's quota. | `CLAIMED` |
| `false` | Login succeeded, but no new quota was reported. | `NO_NEW_GRANT` |
| missing or non-boolean | State is not provable. | `CHECKIN_UNCONFIRMED` |

There is no independent `/checkin` request. The script never calls
`/api/user/checkin`.

## Credentials

Multi-account:

```text
label|username|password
```

Set it as `AGENTROUTER_ACCOUNTS`. Passwords may contain `|`. A single account
can use `AGENTROUTER_USERNAME` and `AGENTROUTER_PASSWORD`.

The default base URL is `https://agentrouter.org`. Set
`AGENTROUTER_BASE_URL=https://ps.air-outer.com` for the domestic site.

## Run

```powershell
python -m pip install -r requirements.txt
$env:AGENTROUTER_USERNAME = "user@example.com"
$env:AGENTROUTER_PASSWORD = "password"
python agentrouter_daily.py
```

Select one account:

```powershell
python agentrouter_daily.py --only 2
```

There is no query-only mode because login itself may grant the daily quota.

## Before And After

Username/password alone do not provide a side-effect-free pre-login account
state read. The output makes that boundary explicit:

- `checked_in=true`: before is false by the server's new-grant semantics and
  after is true.
- `checked_in=false`: before is null and after is false.
- Missing marker: both states remain unconfirmed and the result fails.

If the login returns a session and user ID, the script also reads
`GET /api/user/self` for quota data. A WAF or captcha block is recorded in
`readback_error`; it is not converted into a fake balance change.

## Results

| Result | Meaning |
| :--- | :--- |
| `CLAIMED` | `data.checked_in=true` confirmed a new daily credit. |
| `NO_NEW_GRANT` | Login succeeded and `checked_in=false` was explicit. |
| `CHECKIN_UNCONFIRMED` | The marker was missing or invalid. |
| `STATE_CONFLICT` | Login and user/self disagree on `checked_in`. |
| `AUTH_REJECTED` | Username, password, or session was rejected. |
| `BLOCKED` | HTML challenge instead of JSON. |
| `CONFIG_ERROR` | Environment variables or URL are invalid. |

## Actions

The workflow tests on push and runs the login flow on schedule or manual
dispatch. Configure `AGENTROUTER_ACCOUNTS` or the single-account secrets.
Reports are uploaded as workflow artifacts.

## Test

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check agentrouter_daily.py tests
```

All tests use fake responses and sessions.

## Privacy

Do not commit passwords, sessions, reports, screenshots, or account details.
Only the masked account label is printed.

## License

MIT. See `LICENSE`, `NOTICE.md`, and `THIRD_PARTY_NOTICES.md`.
