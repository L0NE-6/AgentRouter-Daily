# AgentRouter Daily

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · **한국어** · [Português (BR)](README.pt-BR.md)
> 버전: **v1.0.0** (2026-11-24)

AgentRouter의 일일 크레딧은 로그인으로 지급됩니다. 이 도구는 사용자 이름과
비밀번호로 로그인하고 `data.checked_in`을 엄격하게 판정합니다.

## 계약

```text
POST /api/user/login
body: {"username":"...","password":"..."}
```

세션은 `Set-Cookie: session=...`으로 반환됩니다. 로그인 JSON의 `token`
필드는 사용하지 않습니다.

| `data.checked_in` | 의미 | 결과 |
| :--- | :--- | :--- |
| `true` | 이번 로그인으로 당일 크레딧 추가. | `CLAIMED` |
| `false` | 로그인 성공, 새 크레딧 없음. | `NO_NEW_GRANT` |
| 누락 또는 boolean 아님 | 상태 확인 불가. | `CHECKIN_UNCONFIRMED` |

별도 `/checkin`은 없으며 `/api/user/checkin`을 호출하지 않습니다.

## 자격 증명

여러 계정은 `AGENTROUTER_ACCOUNTS`:

```text
label|username|password
```

비밀번호에는 `|`가 포함될 수 있습니다. 단일 계정은
`AGENTROUTER_USERNAME`과 `AGENTROUTER_PASSWORD`를 사용합니다.

기본 URL은 `https://agentrouter.org`입니다. 국내 사이트는
`AGENTROUTER_BASE_URL=https://ps.air-outer.com`을 설정하세요.

## 실행

```powershell
python -m pip install -r requirements.txt
$env:AGENTROUTER_USERNAME = "user@example.com"
$env:AGENTROUTER_PASSWORD = "password"
python agentrouter_daily.py
```

두 번째 계정만 실행:

```powershell
python agentrouter_daily.py --only 2
```

로그인 자체가 크레딧을 지급할 수 있으므로 조회 전용 모드는 없습니다.

## 전후 상태

사용자 이름과 비밀번호만으로는 부작용 없는 로그인 전 상태 조회가 불가능합니다.
출력에서 이 경계를 명시합니다.

- `checked_in=true`: 새 지급 의미에 따라 전 상태 false, 후 상태 true.
- `checked_in=false`: 전 상태 null, 후 상태 false.
- 마커 누락: 전후 모두 미확인이며 실패.

로그인 응답에 session과 사용자 ID가 있으면 `GET /api/user/self`로 크레딧을
보조 확인합니다. WAF 또는 captcha는 `readback_error`에 기록하며 가짜 잔액
변화로 바꾸지 않습니다.

## 결과

| 결과 | 의미 |
| :--- | :--- |
| `CLAIMED` | `checked_in=true`로 새 지급 확인. |
| `NO_NEW_GRANT` | 로그인 성공 및 `checked_in=false` 명시. |
| `CHECKIN_UNCONFIRMED` | 마커 누락 또는 잘못된 타입. |
| `STATE_CONFLICT` | 로그인과 user/self 상태 불일치. |
| `AUTH_REJECTED` | 인증 정보가 거부됨. |
| `BLOCKED` | HTML 인증 페이지 반환. |
| `CONFIG_ERROR` | 환경 변수 또는 URL 오류. |

## Actions

push 시 테스트하고 예약 또는 수동 실행 시 로그인 후 JSON 보고서를
업로드합니다. Secret에 여러 계정 또는 단일 계정 자격 증명을 설정하세요.

## 테스트

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check agentrouter_daily.py tests
```

모든 테스트는 가짜 응답과 세션만 사용합니다.

## 개인정보

비밀번호, session, 보고서, 스크린샷, 계정 정보를 커밋하지 마세요. 스크립트는
마스킹된 계정 라벨만 출력합니다.

## 라이선스

MIT. `LICENSE`, `NOTICE.md`, `THIRD_PARTY_NOTICES.md`를 참고하세요.
