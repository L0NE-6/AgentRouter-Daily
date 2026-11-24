# AgentRouter Daily

[简体中文](../README.md) · [English](README.en.md) · **繁體中文** · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

AgentRouter 的每日額度由登入觸發。本工具使用帳號密碼登入，並嚴格讀取
`data.checked_in` 狀態。

## 介面

```text
POST /api/user/login
body: {"username":"...","password":"..."}
```

登入會透過 `Set-Cookie: session=...` 下發工作階段，不是 JSON `token` 欄位。

| `data.checked_in` | 含義 | 結果 |
| :--- | :--- | :--- |
| `true` | 本次登入新增當日額度。 | `CLAIMED` |
| `false` | 登入成功，但本次沒有新增額度。 | `NO_NEW_GRANT` |
| 缺失或非 boolean | 無法確認狀態。 | `CHECKIN_UNCONFIRMED` |

站點沒有獨立 `/checkin`，腳本不會呼叫 `/api/user/checkin`。

## 憑證

多帳號 `AGENTROUTER_ACCOUNTS`：

```text
備註|使用者名稱|密碼
```

密碼可包含 `|`。單帳號使用 `AGENTROUTER_USERNAME` 與
`AGENTROUTER_PASSWORD`。

預設基址為 `https://agentrouter.org`。國內站可設定
`AGENTROUTER_BASE_URL=https://ps.air-outer.com`。

## 執行

```powershell
python -m pip install -r requirements.txt
$env:AGENTROUTER_USERNAME = "user@example.com"
$env:AGENTROUTER_PASSWORD = "password"
python agentrouter_daily.py
```

只跑第二個帳號：

```powershell
python agentrouter_daily.py --only 2
```

沒有純查詢模式，因為登入本身可能發放當日額度。

## 前後狀態

只有帳號密碼時，無法在登入前安全讀取帳戶狀態。輸出會明確標示：

- `checked_in=true`：依服務端「本次新增額度」語義，前態為 false、後態為 true。
- `checked_in=false`：前態為 null、後態為 false。
- 標記缺失：前後狀態都無法確認，結果失敗。

若登入回應包含 session 與使用者 ID，腳本會再讀取
`GET /api/user/self` 補充額度。WAF 或驗證碼阻擋會寫入
`readback_error`，不會偽造餘額變化。

## 結果

| 結果 | 含義 |
| :--- | :--- |
| `CLAIMED` | `checked_in=true` 確認新增額度。 |
| `NO_NEW_GRANT` | 登入成功且明確 `checked_in=false`。 |
| `CHECKIN_UNCONFIRMED` | 標記缺失或型別錯誤。 |
| `STATE_CONFLICT` | 登入回應與 user/self 狀態衝突。 |
| `AUTH_REJECTED` | 帳號、密碼或工作階段被拒絕。 |
| `BLOCKED` | 返回 HTML 驗證頁。 |
| `CONFIG_ERROR` | 環境變數或 URL 錯誤。 |

## Actions

推送時測試；排程或手動執行時登入並上傳 JSON 報告。請設定
`AGENTROUTER_ACCOUNTS` 或單帳號 Secret。

## 測試

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check agentrouter_daily.py tests
```

全部測試使用假回應與假連線。

## 隱私

不要提交密碼、session、報告、截圖或帳號資訊。腳本只輸出遮罩後的備註。

## 授權

MIT。請見 `LICENSE`、`NOTICE.md` 與 `THIRD_PARTY_NOTICES.md`。
