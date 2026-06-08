# ─────────────────────────────────────────────────────────────
# alerts.py — Telegram-уведомления и инциденты по порогам.
# ─────────────────────────────────────────────────────────────
import json
import time
import urllib.request
import urllib.error
from datetime import datetime

import streamlit as st

import config
from appstate import add_log

try:
    import storage
    STORAGE_AVAILABLE = True
except Exception:
    STORAGE_AVAILABLE = False


# ── Telegram ──────────────────────────────────────────────────
def send_telegram(text, severity="info"):
    token   = st.session_state.get("tg_token","").strip()
    chat_id = st.session_state.get("tg_chat_id","").strip()
    if not token or not chat_id:
        return False, "не задан token или chat_id"
    emoji = {"critical":"🔴","warning":"🟡","ok":"🟢","info":"ℹ️"}.get(severity,"ℹ️")
    payload = json.dumps({"chat_id":chat_id,"text":f"{emoji} BlackArachnia\n{text}"}).encode()
    try:
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload, headers={"Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read().decode())
        if resp.get("ok"): return True, ""
        return False, f"[{resp.get('error_code','')}] {resp.get('description','error')}"
    except urllib.error.HTTPError as e:
        try:
            b = json.loads(e.read().decode())
            return False, f"[{e.code}] {b.get('description', str(e))}"
        except Exception:
            return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)


def tg_alert(key, server, severity, msg):
    if not st.session_state.get("tg_enabled"): return
    now  = time.time()
    last = st.session_state.tg_last_sent.get(key, 0)
    cd   = st.session_state.get("tg_cooldown_min", config.TG_COOLDOWN_MIN) * 60
    if now - last < cd: return
    ok, err = send_telegram(f"{server} — {msg}", severity)
    if ok:
        st.session_state.tg_last_sent[key] = now
        add_log(f"[telegram] алерт: {server} — {msg[:40]}")
    else:
        add_log(f"[telegram] ошибка: {err}")


# ── Инциденты ─────────────────────────────────────────────────
def check_thresholds(name, s):
    th  = st.session_state.thresholds.get(name, dict(config.DEFAULT_THRESHOLDS))
    inc = st.session_state.incidents
    def _open(key, sev, msg):
        for i in inc:
            if i["server"]==name and i["key"]==key and i["status"]=="open": return
        opened = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_id = len(inc)+1
        if STORAGE_AVAILABLE:
            rid = storage.insert_incident(name, key, sev, msg, opened)
            if rid: new_id = rid
        inc.append({"id":new_id,"server":name,"key":key,"severity":sev,"msg":msg,
            "opened":opened,"closed":None,"status":"open"})
        add_log(f"[incident] {sev.upper()} — {name}: {msg}")
        tg_alert(f"{name}_{key}", name, sev, msg)
    def _close(key):
        for i in inc:
            if i["server"]==name and i["key"]==key and i["status"]=="open":
                i["status"]="closed"; i["closed"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if STORAGE_AVAILABLE: storage.update_incident(i["id"],"closed",i["closed"])
    if not s.get("online"):
        _open("offline","critical",f"Сервер недоступен: {s.get('message','')[:50]}"); return
    _close("offline")
    if s.get("cpu") is not None:
        if s["cpu"]>=th["cpu"]: _open("cpu","critical" if s["cpu"]>=95 else "warning",f"CPU {s['cpu']:.0f}% ≥ {th['cpu']}%")
        else: _close("cpu")
    if s.get("ram") is not None:
        if s["ram"]>=th["ram"]: _open("ram","critical" if s["ram"]>=95 else "warning",f"RAM {s['ram']:.0f}% ≥ {th['ram']}%")
        else: _close("ram")
    if s.get("disk") is not None:
        if s["disk"]>=th["disk"]: _open("disk","critical" if s["disk"]>=95 else "warning",f"Disk {s['disk']:.0f}% ≥ {th['disk']}%")
        else: _close("disk")
    sd = s.get("ssl_days",999)
    if sd<config.SSL_CRIT_DAYS: _open("ssl","critical",f"SSL истекает через {sd} дн.")
    elif sd<config.SSL_WARN_DAYS: _open("ssl","warning",f"SSL истекает через {sd} дн.")
    else: _close("ssl")
    if len(inc)>1000: st.session_state.incidents = inc[-1000:]
