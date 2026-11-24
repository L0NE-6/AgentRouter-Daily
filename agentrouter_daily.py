#!/usr/bin/env python3
"""AgentRouter daily credit through the login endpoint with strict state output."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

import requests


PROVIDER = "agentrouter"
DEFAULT_BASE_URL = "https://agentrouter.org"
BASE_URL_ENV = "AGENTROUTER_BASE_URL"
ACCOUNTS_ENV = "AGENTROUTER_ACCOUNTS"
USERNAME_ENV = "AGENTROUTER_USERNAME"
PASSWORD_ENV = "AGENTROUTER_PASSWORD"
LOGIN_PATH = "/api/user/login"
USER_SELF_PATH = "/api/user/self"
REQUEST_TIMEOUT = 25
USER_AGENT = "codex_cli_rs/0.101.0"


class ConfigError(ValueError):
    """Configuration or credential input error."""


class APIError(RuntimeError):
    """Classified API failure."""

    def __init__(
        self,
        result: str,
        message: str,
        *,
        http_status: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.result = result
        self.message = message
        self.http_status = http_status


@dataclass(frozen=True)
class Account:
    note: str
    username: str
    password: str


def emit(payload: Mapping[str, Any]) -> None:
    print(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
        flush=True,
    )


def _safe_label(raw: str, index: int) -> str:
    text = re.sub(r"[\x00-\x1f\x7f\u202a-\u202e\u2066-\u2069]", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "account_%d" % index
    if re.fullmatch(r"1\d{10}", text):
        return text[:3] + "****" + text[-4:]
    if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", text):
        local, domain = text.split("@", 1)
        return (local[:1] or "*") + "***@" + domain
    return text[:64]


def _redact(value: Any, secrets: Sequence[str]) -> str:
    text = str(value)
    unique: list[str] = []
    for secret in secrets:
        secret = str(secret or "")
        if secret and secret not in unique:
            unique.append(secret)
    for secret in sorted(unique, key=len, reverse=True):
        text = text.replace(secret, "[REDACTED]")
    return text


def load_accounts(
    env: Optional[Mapping[str, str]] = None,
) -> list[Account]:
    values = os.environ if env is None else env
    raw = str(values.get(ACCOUNTS_ENV, "") or "")
    accounts: list[Account] = []

    if raw.strip():
        lines = [
            line
            for line in re.split(r"[\r\n]+", raw)
            if line.strip()
        ]
        for index, line in enumerate(lines, 1):
            parts = line.split("|", 2)
            if len(parts) != 3:
                raise ConfigError(
                    "account %d must use label|username|password" % index
                )
            label, username, password = parts
            username = username.strip()
            if not username or not password:
                raise ConfigError(
                    "account %d has an empty username or password" % index
                )
            accounts.append(
                Account(
                    note=_safe_label(label, index),
                    username=username,
                    password=password,
                )
            )
        return accounts

    username = str(values.get(USERNAME_ENV, "") or "").strip()
    password = str(values.get(PASSWORD_ENV, "") or "")
    if not username and not password:
        raise ConfigError(
            "AGENTROUTER_ACCOUNTS or AGENTROUTER_USERNAME + "
            "AGENTROUTER_PASSWORD is not configured"
        )
    if not username or not password:
        raise ConfigError(
            "AGENTROUTER_USERNAME and AGENTROUTER_PASSWORD must both be set"
        )
    return [
        Account(
            note="account_1",
            username=username,
            password=password,
        )
    ]


def resolve_base_url(env: Optional[Mapping[str, str]] = None) -> str:
    values = os.environ if env is None else env
    raw = str(values.get(BASE_URL_ENV, "") or "").strip()
    text = (raw or DEFAULT_BASE_URL).rstrip("/")
    if not text.startswith("https://") and not text.startswith("http://"):
        raise ConfigError("AGENTROUTER_BASE_URL must be an http(s) URL")
    return text


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
    )
    return session


def _login_headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }


def _user_headers(session_cookie: str, user_id: str) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
        "Cookie": "session=" + session_cookie,
        "New-Api-User": user_id,
    }


def _response_text(response: Any) -> str:
    text = getattr(response, "text", "")
    if text:
        return str(text)
    try:
        return json.dumps(response.json(), ensure_ascii=False)
    except Exception:
        return ""


def _payload_message(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    for key in ("message", "msg", "detail", "error"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            nested = _payload_message(value)
            if nested:
                return nested
        elif value not in (None, "", False):
            return str(value)
    data = payload.get("data")
    if isinstance(data, Mapping):
        return _payload_message(data)
    return ""


def _request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    headers: Mapping[str, str],
    secrets: Sequence[str],
    json_body: Optional[Mapping[str, Any]] = None,
    send_json: bool = False,
) -> tuple[Any, int, Any]:
    kwargs: dict[str, Any] = {
        "headers": dict(headers),
        "timeout": REQUEST_TIMEOUT,
        "allow_redirects": False,
    }
    if send_json:
        kwargs["json"] = dict(json_body or {})
    try:
        response = session.request(method, url, **kwargs)
    except requests.RequestException as exc:
        raise APIError(
            "NETWORK_ERROR",
            "network request failed: %s" % _redact(exc, secrets),
        ) from exc

    status = int(getattr(response, "status_code", 0) or 0)
    text = _response_text(response)
    if 300 <= status < 400:
        raise APIError(
            "AUTH_REJECTED",
            "login was redirected (HTTP %d)" % status,
            http_status=status,
        )
    if status in (401, 403):
        raise APIError(
            "AUTH_REJECTED",
            "site rejected the login session (HTTP %d)" % status,
            http_status=status,
        )
    if status == 429:
        raise APIError(
            "RATE_LIMITED",
            "login was rate limited (HTTP %d)" % status,
            http_status=status,
        )
    if not 200 <= status < 300:
        raise APIError(
            "HTTP_ERROR",
            "request failed (HTTP %d)" % status,
            http_status=status,
        )
    if "<html" in text[:500].lower() or "<!doctype" in text[:500].lower():
        raise APIError(
            "BLOCKED",
            "site returned an HTML verification page instead of JSON",
            http_status=status,
        )
    try:
        payload = response.json()
    except Exception as exc:
        raise APIError(
            "INVALID_JSON",
            "response is not JSON: %s" % _redact(exc, secrets),
            http_status=status,
        ) from exc
    if not isinstance(payload, Mapping):
        raise APIError(
            "INVALID_RESPONSE",
            "response is not a JSON object",
            http_status=status,
        )
    if payload.get("success") is False:
        message = _payload_message(payload) or "site rejected the request"
        if re.search(
            r"密码|password|封禁|banned|错误|invalid|credential",
            message,
            re.IGNORECASE,
        ):
            raise APIError(
                "AUTH_REJECTED",
                _redact(message, secrets),
                http_status=status,
            )
        raise APIError(
            "BUSINESS_ERROR",
            _redact(message, secrets),
            http_status=status,
        )
    return payload, status, response


def _number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return int(number) if number.is_integer() else number


def _positive_id(value: Any) -> str:
    if isinstance(value, bool):
        return ""
    text = str(value or "").strip()
    return text if re.fullmatch(r"[1-9][0-9]*", text) else ""


def _session_cookie(response: Any) -> str:
    cookies = getattr(response, "cookies", None)
    getter = getattr(cookies, "get", None)
    if callable(getter):
        try:
            value = getter("session")
        except Exception:
            value = None
        if value:
            return str(value).strip()
    headers = getattr(response, "headers", {}) or {}
    set_cookie = ""
    get_header = getattr(headers, "get", None)
    if callable(get_header):
        set_cookie = str(get_header("Set-Cookie") or "")
    match = re.search(r"(?:^|[;,]\s*)session=([^;,\s]+)", set_cookie)
    return match.group(1) if match else ""


def parse_login(payload: Any, response: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise APIError("INVALID_RESPONSE", "login payload is missing")
    if payload.get("success") is not True:
        raise APIError(
            "INVALID_RESPONSE",
            "login response success field is not true",
        )
    data = payload.get("data")
    if not isinstance(data, Mapping):
        raise APIError(
            "INVALID_RESPONSE",
            "login response has no data object",
        )
    checked_in = data.get("checked_in")
    if not isinstance(checked_in, bool):
        raise APIError(
            "CHECKIN_UNCONFIRMED",
            "login response has no boolean data.checked_in marker",
        )
    quota = _number(data.get("quota"))
    used_quota = _number(data.get("used_quota"))
    balance_total = None
    if quota is not None and used_quota is not None:
        balance_total = quota + used_quota
    return {
        "checked_in": checked_in,
        "quota": quota,
        "used_quota": used_quota,
        "balance_total": balance_total,
        "user_id": _positive_id(data.get("id")),
        "session_cookie": _session_cookie(response),
        "display_name": str(data.get("username") or data.get("display_name") or ""),
    }


def _read_user_self(
    session: requests.Session,
    base_url: str,
    session_cookie: str,
    user_id: str,
    secrets: Sequence[str],
) -> tuple[dict[str, Any], int]:
    payload, status, _ = _request_json(
        session,
        "GET",
        base_url + USER_SELF_PATH,
        headers=_user_headers(session_cookie, user_id),
        secrets=secrets,
    )
    if not isinstance(payload, Mapping):
        raise APIError("INVALID_RESPONSE", "user/self payload is missing")
    data = payload.get("data")
    if not isinstance(data, Mapping):
        raise APIError(
            "INVALID_RESPONSE",
            "user/self response has no data object",
        )
    checked_in = data.get("checked_in")
    quota = _number(data.get("quota"))
    used_quota = _number(data.get("used_quota"))
    return {
        "checked_in": checked_in if isinstance(checked_in, bool) else None,
        "quota": quota,
        "used_quota": used_quota,
        "balance_total": (
            quota + used_quota
            if quota is not None and used_quota is not None
            else None
        ),
    }, status


def _result(
    account: Account,
    result: str,
    ok: bool,
    message: str,
    *,
    http_status: Optional[int] = None,
    claimed: bool = False,
    checked_in: Optional[bool] = None,
    before_state: Optional[Mapping[str, Any]] = None,
    after_state: Optional[Mapping[str, Any]] = None,
    login_accepted: bool = False,
    session_received: bool = False,
    readback_error: Optional[str] = None,
) -> dict[str, Any]:
    payload = {
        "account": account.note,
        "provider": PROVIDER,
        "result": result,
        "ok": ok,
        "message": message,
        "http_status": http_status,
        "login_accepted": login_accepted,
        "session_received": session_received,
        "claimed": claimed,
        "checked_in": checked_in,
        "before_state": dict(before_state or {}),
        "after_state": dict(after_state or {}),
    }
    if readback_error:
        payload["readback_error"] = readback_error
    return payload


def check_account(
    account: Account,
    *,
    base_url: Optional[str] = None,
    session_factory: Callable[[], requests.Session] = make_session,
) -> dict[str, Any]:
    try:
        resolved_base_url = (
            base_url.rstrip("/") if base_url else resolve_base_url()
        )
    except ConfigError as exc:
        return _result(account, "CONFIG_ERROR", False, str(exc))
    secrets = [account.username, account.password]
    session = None
    try:
        session = session_factory()
        raw_login, login_status, login_response = _request_json(
            session,
            "POST",
            resolved_base_url + LOGIN_PATH,
            headers=_login_headers(),
            secrets=secrets,
            json_body={
                "username": account.username,
                "password": account.password,
            },
            send_json=True,
        )
        login = parse_login(raw_login, login_response)
        checked_in = login["checked_in"]
        before_state = (
            {
                "checked_in": False,
                "source": "implied_by_data.checked_in_true",
            }
            if checked_in is True
            else {
                "checked_in": None,
                "source": "not_observable_without_a_pre_login_session",
            }
        )
        after_state = {
            "checked_in": checked_in,
            "quota": login["quota"],
            "used_quota": login["used_quota"],
            "balance_total": login["balance_total"],
            "source": "login_response",
        }
        readback_error = None
        session_received = bool(login["session_cookie"])

        if session_received and login["user_id"]:
            try:
                user_self, _ = _read_user_self(
                    session,
                    resolved_base_url,
                    login["session_cookie"],
                    login["user_id"],
                    secrets,
                )
            except APIError as exc:
                readback_error = "%s: %s" % (exc.result, exc.message)
            else:
                user_checked_in = user_self["checked_in"]
                if (
                    isinstance(user_checked_in, bool)
                    and user_checked_in is not checked_in
                ):
                    after_state.update(user_self)
                    after_state["source"] = "user_self"
                    return _result(
                        account,
                        "STATE_CONFLICT",
                        False,
                        "login response and user/self disagree on checked_in",
                        http_status=login_status,
                        checked_in=checked_in,
                        before_state=before_state,
                        after_state=after_state,
                        login_accepted=True,
                        session_received=True,
                    )
                if user_self["quota"] is not None:
                    after_state["quota"] = user_self["quota"]
                if user_self["used_quota"] is not None:
                    after_state["used_quota"] = user_self["used_quota"]
                if user_self["balance_total"] is not None:
                    after_state["balance_total"] = user_self["balance_total"]
                after_state["source"] = "login_response+user_self"

        if checked_in is True:
            return _result(
                account,
                "CLAIMED",
                True,
                "site confirmed data.checked_in=true for this login",
                http_status=login_status,
                claimed=True,
                checked_in=True,
                before_state=before_state,
                after_state=after_state,
                login_accepted=True,
                session_received=session_received,
                readback_error=readback_error,
            )
        return _result(
            account,
            "NO_NEW_GRANT",
            True,
            "site confirmed data.checked_in=false; no new daily credit was reported",
            http_status=login_status,
            claimed=False,
            checked_in=False,
            before_state=before_state,
            after_state=after_state,
            login_accepted=True,
            session_received=session_received,
            readback_error=readback_error,
        )
    except APIError as exc:
        return _result(
            account,
            exc.result,
            False,
            exc.message,
            http_status=exc.http_status,
        )
    except ConfigError as exc:
        return _result(account, "CONFIG_ERROR", False, str(exc))
    except Exception as exc:
        return _result(
            account,
            "UNEXPECTED_ERROR",
            False,
            "unexpected error: %s" % _redact(exc, secrets),
        )
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()


def run_accounts(
    accounts: Sequence[Account],
    *,
    base_url: Optional[str] = None,
    session_factory: Callable[[], requests.Session] = make_session,
    output: Callable[[Mapping[str, Any]], None] = emit,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for account in accounts:
        result = check_account(
            account,
            base_url=base_url,
            session_factory=session_factory,
        )
        results.append(result)
        output(result)
    return results


def build_summary(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    success = sum(1 for result in results if result.get("ok") is True)
    return {
        "provider": PROVIDER,
        "accounts": len(results),
        "success": success,
        "failed": len(results) - success,
        "claimed_now": sum(
            1 for result in results if result.get("result") == "CLAIMED"
        ),
        "no_new_grant": sum(
            1 for result in results if result.get("result") == "NO_NEW_GRANT"
        ),
        "unconfirmed": sum(
            1
            for result in results
            if result.get("result") == "CHECKIN_UNCONFIRMED"
        ),
        "results": [dict(result) for result in results],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Complete the AgentRouter daily login credit flow."
    )
    parser.add_argument("--only", type=int, default=0)
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    env: Optional[Mapping[str, str]] = None,
    session_factory: Callable[[], requests.Session] = make_session,
    output: Callable[[Mapping[str, Any]], None] = emit,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        accounts = load_accounts(env)
        base_url = resolve_base_url(env)
        if args.only:
            if args.only < 1 or args.only > len(accounts):
                raise ConfigError("--only is outside the configured account range")
            accounts = [accounts[args.only - 1]]
    except ConfigError as exc:
        result = _result(
            Account("config", "", ""),
            "CONFIG_ERROR",
            False,
            str(exc),
        )
        summary = build_summary([result])
        output(result)
        output(summary)
        return 2

    results = run_accounts(
        accounts,
        base_url=base_url,
        session_factory=session_factory,
        output=output,
    )
    summary = build_summary(results)
    output(summary)
    return 0 if summary["failed"] == 0 else 1


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    _configure_utf8_stdio()
    sys.exit(main())
