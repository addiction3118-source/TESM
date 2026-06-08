# ─────────────────────────────────────────────────────────────
# monitoring.py — опрос серверов и обновление кэша состояния.
# ─────────────────────────────────────────────────────────────
import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

import config
from core import check_server, fetch_agent
from appstate import push_metrics, push_uptime
from alerts import check_thresholds

try:
    from applog import get_logger
    log = get_logger()
except Exception:
    import logging
    log = logging.getLogger("blackarachnia")


def _probe_server(name, url, port):
    """Чистая функция (не трогает st.session_state) — безопасна для потоков."""
    r = check_server(url)
    if r["online"]:
        host = url.replace("https://","").replace("http://","").split("/")[0]
        m = fetch_agent(host, port)
        r["cpu"]=m.get("cpu_percent"); r["ram"]=m.get("ram_percent")
        r["ram_used"]=m.get("ram_used_gb"); r["ram_total"]=m.get("ram_total_gb")
        r["disk"]=m.get("disk_percent"); r["disk_used"]=m.get("disk_used_gb")
        r["disk_total"]=m.get("disk_total_gb")
        r["net_up"]=m.get("net_up_kbps"); r["net_down"]=m.get("net_down_kbps")
        r["cores"]=m.get("cpu_cores"); r["load"]=m.get("load_avg")
        r["server_uptime"]=m.get("uptime_sec")  # реальный аптайм сервера
        r["os"]=m.get("os")                      # ОС сервера (для вкладки Службы/Логи)
    return name, r


def refresh_servers():
    # Серверы опрашиваются параллельно (сеть — самое медленное место).
    # Сетевые вызовы — в потоках, запись в session_state — только в основном потоке.
    items = list(st.session_state.servers_dict.items())
    if not items:
        return
    ports = {n: st.session_state.agent_ports.get(n, config.AGENT_DEFAULT_PORT) for n, _ in items}
    results = {}
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(items)))) as ex:
        for fut in [ex.submit(_probe_server, n, u, ports[n]) for n, u in items]:
            try:
                n, r = fut.result()
                results[n] = r
            except Exception:
                pass
    for name, url in items:
        r = results.get(name)
        if r is None:
            continue
        prev = st.session_state.server_cache.get(name, {})
        was_online = prev.get("online")  # None = первая проверка
        if r["online"] and not prev.get("online"):
            st.session_state.uptime_start[name] = time.time()
            if was_online is False:
                log.info(f"{name} ({url}) снова ОНЛАЙН")
        if not r["online"]:
            st.session_state.uptime_start.pop(name, None)
            if was_online or was_online is None:  # переход online→offline или первая проверка
                log.warning(f"{name} ({url}) ОФЛАЙН — {r.get('reason','?')}: {r.get('message','')}")
        st.session_state.server_cache[name] = r
        push_metrics(name, r.get("cpu"), r.get("ram"), r.get("disk"))
        push_uptime(name, r["online"])
        check_thresholds(name, r)
