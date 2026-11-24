# AgentRouter Daily

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · **日本語** · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

AgentRouter の毎日クレジットはログインで付与されます。本ツールはユーザー名と
パスワードでログインし、`data.checked_in` を厳密に判定します。

## 契約

```text
POST /api/user/login
body: {"username":"...","password":"..."}
```

セッションは `Set-Cookie: session=...` で返ります。ログイン本文の JSON
`token` フィールドは使用しません。

| `data.checked_in` | 意味 | 結果 |
| :--- | :--- | :--- |
| `true` | 今回のログインで当日クレジットを追加。 | `CLAIMED` |
| `false` | ログイン成功、今回の追加なし。 | `NO_NEW_GRANT` |
| 欠落または非 boolean | 状態を確認できない。 | `CHECKIN_UNCONFIRMED` |

独立した `/checkin` はなく、`/api/user/checkin` は呼びません。

## 認証情報

複数アカウントは `AGENTROUTER_ACCOUNTS`:

```text
label|username|password
```

パスワードには `|` を含められます。単一アカウントは
`AGENTROUTER_USERNAME` と `AGENTROUTER_PASSWORD` を使用します。

既定のベース URL は `https://agentrouter.org` です。国内サイトは
`AGENTROUTER_BASE_URL=https://ps.air-outer.com` を設定します。

## 実行

```powershell
python -m pip install -r requirements.txt
$env:AGENTROUTER_USERNAME = "user@example.com"
$env:AGENTROUTER_PASSWORD = "password"
python agentrouter_daily.py
```

2 番目のアカウントのみ:

```powershell
python agentrouter_daily.py --only 2
```

ログイン自体がクレジットを付与するため、照会専用モードはありません。

## 前後状態

ユーザー名とパスワードだけでは、副作用なしのログイン前状態取得はできません。
出力では境界を明示します。

- `checked_in=true`: 新規付与の意味から前状態 false、後状態 true。
- `checked_in=false`: 前状態 null、後状態 false。
- マーカー欠落: 前後とも未確認として失敗。

ログイン応答に session とユーザー ID があれば、`GET /api/user/self` で
クレジットを補助確認します。WAF や captcha は `readback_error` に記録し、
架空の残高変化にはしません。

## 結果

| 結果 | 意味 |
| :--- | :--- |
| `CLAIMED` | `checked_in=true` で新規付与を確認。 |
| `NO_NEW_GRANT` | ログイン成功かつ `checked_in=false` が明示。 |
| `CHECKIN_UNCONFIRMED` | マーカー欠落または型不正。 |
| `STATE_CONFLICT` | ログインと user/self の状態が不一致。 |
| `AUTH_REJECTED` | 認証情報が拒否された。 |
| `BLOCKED` | HTML 検証ページが返った。 |
| `CONFIG_ERROR` | 環境変数または URL が不正。 |

## Actions

push 時にテストし、スケジュールまたは手動実行時にログインして JSON
レポートをアップロードします。Secret に複数アカウントまたは単一アカウントの
認証情報を設定してください。

## テスト

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check agentrouter_daily.py tests
```

テストはすべて偽の応答とセッションを使用します。

## プライバシー

パスワード、session、レポート、スクリーンショット、アカウント情報を
コミットしないでください。出力される名前はマスクされます。

## ライセンス

MIT。`LICENSE`、`NOTICE.md`、`THIRD_PARTY_NOTICES.md` を参照してください。
