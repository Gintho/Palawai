import io
import json
import os
import unittest
from unittest import mock

from surf_forecast import web


def call(path, method="GET", body=b"", headers=None, query=""):
    environ = {"PATH_INFO": path, "REQUEST_METHOD": method, "QUERY_STRING": query,
               "CONTENT_LENGTH": str(len(body)), "wsgi.input": io.BytesIO(body)}
    for k, v in (headers or {}).items():
        environ["HTTP_" + k.upper().replace("-", "_")] = v
    out = {}
    res = web.app(environ, lambda s, h: out.setdefault("status", s))
    return int(out["status"].split()[0]), json.loads(b"".join(res))


ENV = {"WEBHOOK_SECRET": "s3cret", "TELEGRAM_CHAT_ID": "42",
       "TELEGRAM_BOT_TOKEN": "x"}


@mock.patch.dict(os.environ, ENV)
class WebTest(unittest.TestCase):
    def msg(self, chat, text, secret="s3cret"):
        body = json.dumps({"message": {"chat": {"id": chat}, "text": text}}).encode()
        return call("/api/telegram", "POST", body, {"X-Telegram-Bot-Api-Secret-Token": secret})

    @mock.patch.object(web.telegram, "call")
    @mock.patch.object(web.service, "send_forecast")
    def test_surf_sends_forecast(self, send, tg):
        self.assertEqual(self.msg(42, "Surf")[0], 200)
        send.assert_called_once_with("42")

    @mock.patch.object(web.telegram, "send")
    @mock.patch.object(web.service, "send_forecast")
    def test_other_text_sends_help(self, send, tg_send):
        self.msg(42, "salut")
        send.assert_not_called()
        tg_send.assert_called_once()

    @mock.patch.object(web.service, "send_forecast")
    def test_stranger_and_bad_secret_ignored(self, send):
        self.assertEqual(self.msg(7, "surf")[0], 200)
        self.assertEqual(self.msg(42, "surf", secret="nope")[0], 401)
        send.assert_not_called()

    @mock.patch.object(web.service, "send_forecast")
    def test_no_automatic_send_route(self, send):
        call("/api/cron")
        send.assert_not_called()

    def test_setup_requires_key(self):
        self.assertEqual(call("/api/setup", query="key=bad")[0], 401)


if __name__ == "__main__":
    unittest.main()
