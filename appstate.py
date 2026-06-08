# ─────────────────────────────────────────────────────────────
# appstate.py — состояние приложения и связанные хелперы.
#
# Журнал/аудит, история метрик и аптайма, отчёт. Работают поверх
# st.session_state (рабочий кэш) с write-through в SQLite (storage).
# ─────────────────────────────────────────────────────────────
import os
import time
import datetime as dt
from datetime import datetime

import streamlit as st

try:
    import storage
    STORAGE_AVAILABLE = True
except Exception:
    STORAGE_AVAILABLE = False


def load_keys_from_env():
    return {"groq":os.getenv("GROQ_API_KEY",""),"gemini":os.getenv("GEMINI_API_KEY",""),
            "openai":os.getenv("OPENAI_API_KEY","")}


def add_log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{ts}] {msg}")
    if len(st.session_state.logs) > 300:
        st.session_state.logs = st.session_state.logs[-300:]


def add_audit(server, cmd, rc):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.audit_log.append({"ts":ts,"server":server,"cmd":cmd,"rc":rc})
    if len(st.session_state.audit_log) > 500:
        st.session_state.audit_log = st.session_state.audit_log[-500:]
    if STORAGE_AVAILABLE:
        storage.insert_audit(ts, server, cmd, rc)


# ── Uptime 90 дней ────────────────────────────────────────────
def push_uptime(name, online):
    today = datetime.now().strftime("%Y-%m-%d")
    h = st.session_state.uptime_history.setdefault(name, {})
    d = h.get(today, {"checks":0,"up":0})
    d["checks"]+=1
    if online: d["up"]+=1
    h[today]=d
    if STORAGE_AVAILABLE:
        storage.upsert_uptime(name, today, d["checks"], d["up"])


def get_uptime_pct(name, days=90):
    h = st.session_state.uptime_history.get(name, {})
    total=up=0
    cutoff=(datetime.now()-dt.timedelta(days=days)).strftime("%Y-%m-%d")
    for day,v in h.items():
        if day>=cutoff: total+=v["checks"]; up+=v["up"]
    return (up/total*100) if total else None


def uptime_grid(name, days=90):
    h = st.session_state.uptime_history.get(name, {})
    cells=[]
    for i in range(days-1,-1,-1):
        day=(datetime.now()-dt.timedelta(days=i)).strftime("%Y-%m-%d")
        v=h.get(day)
        if v is None: c="#2a1a3d"; tip=f"{day}: нет данных"
        else:
            pct=v["up"]/v["checks"]*100 if v["checks"] else 0
            c="#3fb950" if pct>=99 else "#e3b341" if pct>=90 else "#f85149"
            tip=f"{day}: {pct:.1f}%"
        cells.append(f'<div class="upt-cell" style="background:{c}" title="{tip}"></div>')
    return '<div class="upt-grid">'+"".join(cells)+'</div>'


# ── Метрики (sparkline) ───────────────────────────────────────
def push_metrics(name, cpu, ram, disk=None):
    h = st.session_state.metrics_history.setdefault(name, {"cpu":[],"ram":[],"disk":[]})
    for k,v in [("cpu",cpu),("ram",ram),("disk",disk)]:
        if v is not None:
            h[k].append(round(v,1)); h[k]=h[k][-60:]
    if STORAGE_AVAILABLE:
        storage.insert_metric(name, time.time(),
            round(cpu,1)  if cpu  is not None else None,
            round(ram,1)  if ram  is not None else None,
            round(disk,1) if disk is not None else None)


# ── Отчёт (Markdown) ──────────────────────────────────────────
def build_report():
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    L=["# BlackArachnia Report",f"**{now}**",""]
    for name,url in st.session_state.servers_dict.items():
        s=st.session_state.server_cache.get(name); upt=get_uptime_pct(name)
        L.append(f"## {name} — {url}")
        if not s: L.append("*Не проверялся*\n"); continue
        L.append(f"- Статус: {'🟢 Online' if s['online'] else '🔴 Offline'}")
        L.append(f"- HTTP {s.get('status_code','—')} | IP {s.get('ip','—')} | SSL {s.get('ssl_days','—')}д")
        if upt is not None: L.append(f"- Uptime 90д: {upt:.2f}%")
        if s.get("cpu") is not None:
            L.append(f"- CPU {s['cpu']:.0f}% | RAM {s['ram']:.0f}% | Disk {s.get('disk',0):.0f}%")
        L.append("")
    op=[i for i in st.session_state.incidents if i["status"]=="open"]
    if op:
        L.append(f"## Активные инциденты ({len(op)})")
        for i in op: L.append(f"- [{i['severity'].upper()}] {i['server']}: {i['msg']} ({i['opened']})")
    return "\n".join(L)
