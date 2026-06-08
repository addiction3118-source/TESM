# Тесты чистых функций core.py: классификатор LLM-роутера, валидация,
# форматирование, классификация сетевых ошибок и check_server (с моками).
import socket
import ssl
import urllib.error
import urllib.request

import core


# ── classify (LLM-роутер) ─────────────────────────────────────
def test_classify_code():
    assert core.classify("напиши функцию на python") == "code"
    assert core.classify("give me a bash command") == "code"
    assert core.classify("SELECT * FROM users (sql)") == "code"


def test_classify_reasoning():
    assert core.classify("почему сервер тормозит") == "reasoning"
    assert core.classify("сравни нагрузку серверов") == "reasoning"
    assert core.classify("объясни эту ошибку") == "reasoning"


def test_classify_long():
    assert core.classify("a" * 16001) == "long"


def test_classify_general():
    assert core.classify("привет, как дела") == "general"


# ── is_valid_hostname ─────────────────────────────────────────
def test_valid_hostname_ok():
    ok, msg = core.is_valid_hostname("luat.ru")
    assert ok is True and msg == ""


def test_valid_hostname_empty():
    assert core.is_valid_hostname("")[0] is False


def test_valid_hostname_bad_chars():
    ok, msg = core.is_valid_hostname("bad host!")
    assert ok is False and msg == "Недопустимые символы"


def test_valid_hostname_no_dot():
    ok, msg = core.is_valid_hostname("localhost")
    assert ok is False and msg == "Неполный домен"


# ── fmt_uptime ────────────────────────────────────────────────
def test_fmt_uptime():
    assert core.fmt_uptime(30) == "30s"
    assert core.fmt_uptime(90) == "1m 30s"
    assert core.fmt_uptime(3700) == "1h 1m"
    assert core.fmt_uptime(90000) == "1d 1h"


# ── _net_reason (классификация ошибок) ────────────────────────
def test_net_reason_timeout():
    assert core._net_reason(socket.timeout()) == "timeout"
    assert core._net_reason(TimeoutError()) == "timeout"


def test_net_reason_dns():
    assert core._net_reason(socket.gaierror()) == "dns"


def test_net_reason_refused():
    assert core._net_reason(ConnectionRefusedError()) == "refused"


def test_net_reason_ssl():
    assert core._net_reason(ssl.SSLError()) == "ssl"


def test_net_reason_http():
    he = urllib.error.HTTPError("http://x", 403, "Forbidden", None, None)
    assert core._net_reason(he) == "http_403"


def test_net_reason_urlerror_wraps_cause():
    assert core._net_reason(urllib.error.URLError(socket.timeout())) == "timeout"
    assert core._net_reason(urllib.error.URLError(socket.gaierror())) == "dns"


# ── _reason_msg ───────────────────────────────────────────────
def test_reason_msg():
    assert core._reason_msg("timeout") == "таймаут"
    assert core._reason_msg("http_403") == "HTTP 403"
    assert core._reason_msg("net:boom") == "сеть: boom"
    assert core._reason_msg("unknown", "запасной") == "запасной"


# ── check_server (моки, без реальной сети) ────────────────────
def test_check_server_refused(monkeypatch):
    def boom(*a, **k):
        raise ConnectionRefusedError()
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    r = core.check_server("example.test")
    assert r["online"] is False
    assert r["reason"] == "refused"
    assert r["message"] == "соединение отклонено"


def test_check_server_timeout(monkeypatch):
    def boom(*a, **k):
        raise socket.timeout()
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    r = core.check_server("example.test")
    assert r["reason"] == "timeout"
    assert r["online"] is False


def test_check_server_success(monkeypatch):
    class FakeResp:
        def getcode(self):
            return 200
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: FakeResp())
    # Отключаем реальные SSL/DNS вызовы внутри check_server.
    monkeypatch.setattr(socket, "create_connection",
                        lambda *a, **k: (_ for _ in ()).throw(OSError()))
    monkeypatch.setattr(socket, "gethostbyname", lambda h: "1.2.3.4")
    r = core.check_server("example.test")
    assert r["online"] is True
    assert r["status_code"] == 200
    assert r["ip"] == "1.2.3.4"
    assert r["reason"] == "ok"
