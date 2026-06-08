# ─────────────────────────────────────────────────────────────
# core.py — чистые функции BlackArachnia без зависимости от Streamlit.
#
# Вынесены сюда из app.py, чтобы их можно было покрыть юнит-тестами
# (pytest) отдельно от UI: импорт app.py выполняет весь Streamlit-интерфейс,
# а core.py импортируется без побочных эффектов.
#
# Здесь только сетевые / классификационные / валидационные хелперы,
# не трогающие st.session_state. Это НЕ полная разбивка монолита.
# ─────────────────────────────────────────────────────────────
import re
import json
import socket
import ssl
import urllib.request
import urllib.error
import datetime as dt
from datetime import datetime

import config

try:
    from applog import get_logger
    log = get_logger()
except Exception:
    import logging
    log = logging.getLogger("blackarachnia")


# ── Классификация сетевых ошибок ──────────────────────────────
def _net_reason(e):
    """Классифицирует сетевую ошибку в короткую причину:
    timeout / dns / refused / ssl / http_NNN / <ИмяИсключения>."""
    if isinstance(e, urllib.error.HTTPError): return f"http_{e.code}"
    if isinstance(e, (TimeoutError, socket.timeout)): return "timeout"
    if isinstance(e, socket.gaierror): return "dns"
    if isinstance(e, ssl.SSLError): return "ssl"
    if isinstance(e, ConnectionRefusedError): return "refused"
    if isinstance(e, urllib.error.URLError):
        r = getattr(e, "reason", None)
        if isinstance(r, (TimeoutError, socket.timeout)): return "timeout"
        if isinstance(r, socket.gaierror): return "dns"
        if isinstance(r, ssl.SSLError): return "ssl"
        if isinstance(r, ConnectionRefusedError): return "refused"
        return f"net:{r}"
    return type(e).__name__


# Человекочитаемые причины для UI
_REASON_RU = {"timeout":"таймаут","dns":"DNS не разрешается",
              "refused":"соединение отклонено","ssl":"ошибка SSL"}


def _reason_msg(reason, fallback=""):
    if reason.startswith("http_"): return f"HTTP {reason[5:]}"
    if reason.startswith("net:"):  return f"сеть: {reason[4:]}"
    return _REASON_RU.get(reason, fallback or reason)


# ── Валидация / форматирование ────────────────────────────────
def is_valid_hostname(h):
    if not h or not h.strip(): return False,"Адрес не может быть пустым"
    if not re.match(r"^[a-zA-Z0-9.\-]+$", h): return False,"Недопустимые символы"
    if not re.search(r"\.", h): return False,"Неполный домен"
    return True,""


def fmt_uptime(s):
    if s<60: return f"{int(s)}s"
    if s<3600: return f"{int(s//60)}m {int(s%60)}s"
    if s<86400: return f"{int(s//3600)}h {int((s%3600)//60)}m"
    return f"{int(s//86400)}d {int((s%86400)//3600)}h"


# ── LLM-роутер (классификация запроса) ────────────────────────
def classify(p):
    if len(p)>16000: return "long"
    if re.search(r"\b(код|code|python|sql|bash|функци|class)\b",p,re.I): return "code"
    if re.search(r"\b(почему|объясни|why|analyze|проанализир|сравни)\b",p,re.I): return "reasoning"
    return "general"


# ── Проверка сервера ──────────────────────────────────────────
def check_server(url):
    host = url.replace("https://","").replace("http://","").split("/")[0]
    hdr  = {"User-Agent":"Mozilla/5.0"}
    last_err = None
    for scheme in ("https","http"):
        try:
            r = urllib.request.urlopen(urllib.request.Request(f"{scheme}://{host}",headers=hdr), timeout=config.HTTP_CHECK_TIMEOUT)
            ssl_days=0
            if scheme=="https":
                try:
                    ctx=ssl.create_default_context()
                    with socket.create_connection((host,443),timeout=config.SSL_CONNECT_TIMEOUT) as sk:
                        with ctx.wrap_socket(sk,server_hostname=host) as ss:
                            exp=datetime.strptime(ss.getpeercert()["notAfter"],"%b %d %H:%M:%S %Y %Z")
                            ssl_days=(exp-datetime.now(dt.UTC).replace(tzinfo=None)).days
                except Exception: pass
            try: ip=socket.gethostbyname(host)
            except Exception: ip="—"
            return {"online":True,"status_code":r.getcode(),"ip":ip,"ssl_days":ssl_days,
                    "reason":"ok","message":"OK","last_seen":datetime.now().strftime("%H:%M:%S")}
        except Exception as e:
            last_err=e; continue
    # Оба протокола не ответили — классифицируем причину последней ошибки.
    reason = _net_reason(last_err) if last_err is not None else "error"
    msg = _reason_msg(reason, fallback=str(last_err)[:60] if last_err is not None else "недоступен")
    return {"online":False,"status_code":"—","ip":"—","ssl_days":0,
            "reason":reason,"message":msg,"last_seen":"—"}


def fetch_agent(host, port=config.AGENT_DEFAULT_PORT, path="/metrics"):
    try:
        req=urllib.request.Request(f"http://{host}:{port}{path}",headers={"User-Agent":"BA/3"})
        with urllib.request.urlopen(req,timeout=config.AGENT_FETCH_TIMEOUT) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        # Периодический опрос: пишем в DEBUG (в файл не попадает — без спама),
        # но причина доступна при включении DEBUG-уровня.
        log.debug(f"agent {host}:{port}{path} недоступен — {_net_reason(e)}")
        return {}


def exec_remote(host, cmd, port=config.AGENT_DEFAULT_PORT, token=""):
    try:
        payload=json.dumps({"cmd":cmd,"token":token}).encode()
        req=urllib.request.Request(f"http://{host}:{port}/exec",data=payload,
            headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=config.EXEC_TIMEOUT) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try: msg=json.loads(e.read().decode()).get("error",f"HTTP {e.code}")
        except Exception: msg=f"HTTP {e.code}"
        log.warning(f"exec {host}:{port}: HTTP {e.code} — {msg}")
        return {"error":msg}
    except Exception as e:
        reason=_net_reason(e)
        log.warning(f"exec {host}:{port}: {reason} — {e}")
        return {"error":_reason_msg(reason, fallback=str(e))}
