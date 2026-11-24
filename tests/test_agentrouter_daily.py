import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import agentrouter_daily


class FakeResponse:
    def __init__(
        self,
        payload=None,
        *,
        status_code=200,
        text=None,
        cookies=None,
        headers=None,
    ):
        self.status_code = status_code
        self.payload = payload
        self.text = (
            text
            if text is not None
            else json.dumps(payload, ensure_ascii=False)
            if payload is not None
            else ""
        )
        self.cookies = cookies or {}
        self.headers = headers or {}

    def json(self):
        if self.payload is None:
            raise ValueError("no json")
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.closed = False

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)

    def close(self):
        self.closed = True


class SessionFactory:
    def __init__(self, groups):
        self.groups = [list(group) for group in groups]
        self.sessions = []

    def __call__(self):
        session = FakeSession(self.groups.pop(0))
        self.sessions.append(session)
        return session


def login_response(
    checked=True,
    *,
    user_id=42,
    quota=1000,
    used_quota=500,
    session="session-secret",
):
    data = {
        "id": user_id,
        "username": "example-user",
        "checked_in": checked,
        "quota": quota,
        "used_quota": used_quota,
    }
    return FakeResponse(
        {"success": True, "data": data},
        cookies={"session": session} if session else {},
        headers=(
            {"Set-Cookie": "session=" + session + "; Path=/; HttpOnly"}
            if session
            else {}
        ),
    )


def user_self_response(checked=None, *, quota=1100, used_quota=500):
    data = {"quota": quota, "used_quota": used_quota}
    if checked is not None:
        data["checked_in"] = checked
    return FakeResponse({"success": True, "data": data})


def account():
    return agentrouter_daily.load_accounts(
        {
            "AGENTROUTER_USERNAME": "site-user",
            "AGENTROUTER_PASSWORD": "site-pass",
        }
    )[0]


class AgentRouterDailyTests(unittest.TestCase):
    def test_load_multi_account_and_password_with_pipe(self):
        accounts = agentrouter_daily.load_accounts(
            {
                "AGENTROUTER_ACCOUNTS": (
                    "demo@example.com|user-one|pass|with|pipe\n"
                    "second|user-two|plain\n"
                    "third|user-three|  spaced pass  "
                )
            }
        )
        self.assertEqual(3, len(accounts))
        self.assertEqual("d***@example.com", accounts[0].note)
        self.assertEqual("pass|with|pipe", accounts[0].password)
        self.assertEqual("user-two", accounts[1].username)
        self.assertEqual("  spaced pass  ", accounts[2].password)

    def test_checked_in_true_claims_and_reads_user_self(self):
        factory = SessionFactory(
            [[login_response(True), user_self_response(True)]]
        )
        result = agentrouter_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("CLAIMED", result["result"])
        self.assertTrue(result["ok"])
        self.assertTrue(result["claimed"])
        self.assertFalse(result["before_state"]["checked_in"])
        self.assertTrue(result["after_state"]["checked_in"])
        self.assertEqual(
            "login_response+user_self",
            result["after_state"]["source"],
        )

        calls = factory.sessions[0].calls
        self.assertEqual(["POST", "GET"], [call[0] for call in calls])
        login_kwargs = calls[0][2]
        self.assertEqual(
            {"username": "site-user", "password": "site-pass"},
            login_kwargs["json"],
        )
        self.assertNotIn("Authorization", login_kwargs["headers"])
        self.assertNotIn("Cookie", login_kwargs["headers"])
        self.assertEqual(
            "session=session-secret",
            calls[1][2]["headers"]["Cookie"],
        )
        self.assertEqual("42", calls[1][2]["headers"]["New-Api-User"])

    def test_checked_in_false_is_explicit_no_new_grant(self):
        factory = SessionFactory([[login_response(False, session="")]])
        result = agentrouter_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("NO_NEW_GRANT", result["result"])
        self.assertTrue(result["ok"])
        self.assertFalse(result["claimed"])
        self.assertIsNone(result["before_state"]["checked_in"])
        self.assertFalse(result["after_state"]["checked_in"])
        self.assertIn("no new daily credit", result["message"])

    def test_missing_checked_in_is_unconfirmed(self):
        payload = {
            "success": True,
            "data": {"id": 42, "quota": 1000, "used_quota": 500},
        }
        factory = SessionFactory([[FakeResponse(payload)]])
        result = agentrouter_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("CHECKIN_UNCONFIRMED", result["result"])
        self.assertFalse(result["ok"])

    def test_non_boolean_checked_in_is_unconfirmed(self):
        payload = {
            "success": True,
            "data": {"id": 42, "checked_in": "true"},
        }
        factory = SessionFactory([[FakeResponse(payload)]])
        result = agentrouter_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("CHECKIN_UNCONFIRMED", result["result"])
        self.assertFalse(result["ok"])

    def test_state_conflict_between_login_and_user_self(self):
        factory = SessionFactory(
            [[login_response(True), user_self_response(False)]]
        )
        result = agentrouter_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("STATE_CONFLICT", result["result"])
        self.assertFalse(result["ok"])

    def test_user_self_block_does_not_erase_login_state(self):
        factory = SessionFactory(
            [
                [
                    login_response(True),
                    FakeResponse({"message": "expired"}, status_code=401),
                ]
            ]
        )
        result = agentrouter_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("CLAIMED", result["result"])
        self.assertTrue(result["ok"])
        self.assertEqual("AUTH_REJECTED: site rejected the login session (HTTP 401)", result["readback_error"])

    def test_wrong_password_is_auth_rejected_and_redacted(self):
        factory = SessionFactory(
            [
                [
                    FakeResponse(
                        {
                            "success": False,
                            "message": "用户名或密码错误 site-pass",
                        }
                    )
                ]
            ]
        )
        result = agentrouter_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        rendered = json.dumps(result, ensure_ascii=False)
        self.assertEqual("AUTH_REJECTED", result["result"])
        self.assertFalse(result["ok"])
        self.assertNotIn("site-pass", rendered)
        self.assertIn("[REDACTED]", rendered)

    def test_html_challenge_is_blocked(self):
        factory = SessionFactory(
            [
                [
                    FakeResponse(
                        text="<!doctype html><html>captcha</html>",
                    )
                ]
            ]
        )
        result = agentrouter_daily.check_account(
            account(),
            base_url="https://example.test",
            session_factory=factory,
        )
        self.assertEqual("BLOCKED", result["result"])
        self.assertFalse(result["ok"])

    def test_multi_account_isolation(self):
        accounts = agentrouter_daily.load_accounts(
            {
                "AGENTROUTER_ACCOUNTS": (
                    "one|user-one|pass-one\n"
                    "two|user-two|pass-two"
                )
            }
        )
        factory = SessionFactory(
            [
                [login_response(True, session="")],
                [
                    FakeResponse(
                        {"success": False, "message": "密码错误"},
                    )
                ],
            ]
        )
        results = agentrouter_daily.run_accounts(
            accounts,
            base_url="https://example.test",
            session_factory=factory,
            output=lambda _: None,
        )
        self.assertEqual("CLAIMED", results[0]["result"])
        self.assertEqual("AUTH_REJECTED", results[1]["result"])
        self.assertIsNot(factory.sessions[0], factory.sessions[1])
        self.assertTrue(all(session.closed for session in factory.sessions))

    def test_default_base_url(self):
        self.assertEqual(
            "https://agentrouter.org",
            agentrouter_daily.resolve_base_url({}),
        )
        self.assertEqual(
            "https://agentrouter.org",
            agentrouter_daily.resolve_base_url({"AGENTROUTER_BASE_URL": ""}),
        )

    def test_config_error_summary(self):
        output = []
        code = agentrouter_daily.main(
            [],
            env={},
            session_factory=SessionFactory([]),
            output=output.append,
        )
        self.assertEqual(2, code)
        self.assertEqual("CONFIG_ERROR", output[0]["result"])
        self.assertEqual("agentrouter", output[-1]["provider"])


if __name__ == "__main__":
    unittest.main()
