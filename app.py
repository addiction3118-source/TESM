import streamlit as st
import time, re, json, os
from datetime import datetime

# ── Загрузка .env (ключи API + Telegram) ──────────────────────
def _load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())
_load_dotenv()

try:
    from keys_store import save_keys, load_keys, keys_file_exists
    KEYS_STORE_AVAILABLE = True
except ImportError:
    KEYS_STORE_AVAILABLE = False

# Персистентность состояния (SQLite). Если модуль/БД недоступны — приложение
# работает как раньше (всё в памяти), просто без сохранения между запусками.
try:
    import storage
    storage.init_db()
    STORAGE_AVAILABLE = True
except Exception as _e:
    STORAGE_AVAILABLE = False
    print(f"[storage] init failed: {_e}")

# Файловое логирование (различение причин сетевых ошибок).
try:
    from applog import get_logger
    log = get_logger()
except Exception:
    import logging as _logging
    log = _logging.getLogger("blackarachnia")  # тихий фоллбэк, если applog недоступен

# Чистые функции (сеть/классификация/валидация) вынесены в core.py —
# чтобы их можно было тестировать отдельно от Streamlit-UI.
from core import (check_server, fetch_agent, exec_remote,
                  is_valid_hostname, fmt_uptime)

# Единая точка настройки (пороги, модели, порты, таймауты, антиспам).
import config
# Команды служб/логов под ОС сервера (Linux/Windows).
import platform_cmds
# Визуальные компоненты (гейджи, спарклайны, бары).
from widgets import _color, bar, sparkline, radial_gauge
# Состояние: журнал/аудит, история метрик и аптайма, отчёт.
from appstate import (load_keys_from_env, add_log, add_audit, push_uptime,
                      get_uptime_pct, uptime_grid, build_report)
# Алерты: Telegram + инциденты по порогам.
from alerts import send_telegram, check_thresholds
# Опрос серверов и LLM-роутер.
from monitoring import refresh_servers
from llm import route_and_call, build_context
import styles
from i18n import T

st.set_page_config(page_title="BlackArachnia", page_icon="🕷️",
                   layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════
#  ПУТИ + АВТОВХОД
# ═══════════════════════════════════════════════════════════════
_DIR          = os.path.dirname(os.path.abspath(__file__))
_JSON_PATH    = os.path.join(_DIR, "temp_servers.json")

# «Запомнить меня»: мастер-пароль хранится в ОС-хранилище (keyring) с TTL,
# а не в обратимом XOR-файле. Логика вынесена в session_store.py.
from session_store import (save_session, load_session, clear_session,
                           has_session, available as session_available)

# CSS-тема вынесена в styles.py
styles.inject()


# ═══════════════════════════════════════════════════════════════
#  ЭКРАН ВХОДА
# ═══════════════════════════════════════════════════════════════
if "keys_unlocked" not in st.session_state: st.session_state.keys_unlocked=False
if "api_keys" not in st.session_state: st.session_state.api_keys=load_keys_from_env()

if KEYS_STORE_AVAILABLE and not st.session_state.keys_unlocked:
    if keys_file_exists():
        sp=load_session()
        if sp:
            loaded=load_keys(sp)
            if loaded is not None:
                st.session_state.api_keys=loaded
                st.session_state.keys_unlocked=True
                st.rerun()
            else:
                clear_session()
        st.markdown("""<div style="max-width:360px;margin:80px auto;padding:32px;
            background:#150d24;border:1px solid #3d2459;border-radius:12px;text-align:center">
            <div style="font-size:28px;margin-bottom:8px">🕷️</div>
            <div style="font-size:16px;font-weight:600;color:#e6edf3">BlackArachnia</div>
            <div style="font-size:12px;color:#6e7681;margin-top:4px">Введи пароль для расшифровки ключей</div>
            </div>""", unsafe_allow_html=True)
        _,cc,_=st.columns([1,2,1])
        with cc:
            pwd=st.text_input("Ввод",type="password",key="unlock_pwd",placeholder="Пароль...")
            remember=st.checkbox("Запомнить меня на этом устройстве",value=True,key="chk_remember") if session_available() else False
            if st.button("Войти",key="btn_unlock",use_container_width=True):
                loaded=load_keys(pwd)
                if loaded is not None:
                    st.session_state.api_keys=loaded
                    st.session_state.keys_unlocked=True
                    if remember: save_session(pwd)
                    st.rerun()
                else: st.error("Неверный пароль")
            if config.ALLOW_SKIP_KEYS and st.button("Войти без ключей",key="btn_skip",use_container_width=True):
                st.session_state.keys_unlocked=True; st.rerun()
        st.stop()
    else:
        st.session_state.keys_unlocked=True

# ═══════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════
if "servers_dict" not in st.session_state:
    if os.path.exists(_JSON_PATH):
        with open(_JSON_PATH,encoding="utf-8") as f: loaded=json.load(f)
        st.session_state.servers_dict=loaded if loaded else {"ЛАТ":"luat.ru"}
    else:
        st.session_state.servers_dict={"ЛАТ":"luat.ru"}

for k,v in [
    ("logs",["[info] BlackArachnia v3 запущен."]),("server_cache",{}),("uptime_start",{}),
    ("chat_messages",[]),("agent_token",""),("agent_ports",{}),("term_history",[]),
    ("term_cmd_history",[]),("audit_log",[]),("metrics_history",{}),("uptime_history",{}),
    ("incidents",[]),("thresholds",{}),("monitoring_active",True),("lang","ru"),
    ("tg_token",os.getenv("TG_BOT_TOKEN","")),("tg_chat_id",os.getenv("TG_CHAT_ID","")),
    ("tg_enabled",bool(os.getenv("TG_BOT_TOKEN","") and os.getenv("TG_CHAT_ID",""))),
    ("tg_cooldown_min",config.TG_COOLDOWN_MIN),("tg_last_sent",{}),
    ("system_prompt","Ты — ассистент мониторинга серверов BlackArachnia. Помогай кратко и по делу."),
    ("term_snippets",[
        {"name":"Disk","cmd":"df -h"},{"name":"Memory","cmd":"free -h"},
        {"name":"Top CPU","cmd":"ps aux --sort=-%cpu | head -12"},
        {"name":"Ports","cmd":"ss -tlnp"},{"name":"Nginx","cmd":"systemctl status nginx --no-pager -l"},
        {"name":"Docker","cmd":"docker ps"},{"name":"Journal","cmd":"journalctl -n 40 --no-pager"},
    ]),
]:
    if k not in st.session_state: st.session_state[k]=v

# Загрузка сохранённого состояния из SQLite (один раз на сессию).
# Перезаписывает пустые дефолты выше данными из БД.
if STORAGE_AVAILABLE and "storage_loaded" not in st.session_state:
    st.session_state.incidents       = storage.load_incidents()
    st.session_state.metrics_history = storage.load_metrics_history()
    st.session_state.uptime_history  = storage.load_uptime_history()
    st.session_state.audit_log       = storage.load_audit()
    st.session_state.storage_loaded  = True

# ═══════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════
def _sb_label(txt, top=False):
    border = "border-top:1px solid #2a1a3d;padding-top:10px;" if top else ""
    st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin:10px 0 4px;{border}">{txt}</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""<div style="padding:14px 0 10px;text-align:center;border-bottom:1px solid #2a1a3d;margin-bottom:10px">
      <div style="font-size:17px;font-weight:700;color:#e6edf3">🕷️ BlackArachnia</div>
      <div style="font-size:10px;color:#6e7681;margin-top:2px">SERVER MONITOR v3</div></div>""", unsafe_allow_html=True)

    _sb_label("ЯЗЫК / LANGUAGE")
    lc1,lc2=st.columns(2)
    if lc1.button("🇷🇺 RU",key="lang_ru",use_container_width=True): st.session_state.lang="ru"; st.rerun()
    if lc2.button("🇬🇧 EN",key="lang_en",use_container_width=True): st.session_state.lang="en"; st.rerun()

    _sb_label(T("monitoring"),top=True)
    st.toggle(T("auto_refresh"),value=st.session_state.monitoring_active,key="mon_toggle",
              on_change=lambda: st.session_state.update(monitoring_active=st.session_state.mon_toggle))

    open_inc=[i for i in st.session_state.incidents if i["status"]=="open"]
    if open_inc:
        c=sum(1 for i in open_inc if i["severity"]=="critical"); w=len(open_inc)-c
        parts=[]
        if c: parts.append(f'<span style="color:#f85149">⬤ {c}</span>')
        if w: parts.append(f'<span style="color:#e3b341">⬤ {w}</span>')
        st.markdown(f'<div style="font-size:11px;margin:4px 0 8px;padding:6px 8px;background:#1a1f27;border-radius:6px;border:1px solid #2a1a3d">Инциденты: {" ".join(parts)}</div>',unsafe_allow_html=True)

    _sb_label(T("environment"),top=True)
    env_list=list(st.session_state.servers_dict.keys())
    env_choice=st.selectbox("Выбор",env_list,key="main_select",label_visibility="collapsed")
    server_url=st.session_state.servers_dict.get(env_choice,"")

    _sb_label(T("api_keys"),top=True)
    for _p,_l in [("groq","Groq"),("gemini","Gemini"),("openai","OpenAI")]:
        _cur=st.session_state.api_keys.get(_p,"")
        _col="#3fb950" if _cur else "#f85149"
        st.markdown(f'<div style="display:flex;justify-content:space-between;padding:2px 0"><span style="font-size:11px;color:#8b949e">{_l}</span><span style="font-size:9px;color:{_col}">{"●" if _cur else "○"}</span></div>',unsafe_allow_html=True)
        _new=st.text_input("Ввод",value=_cur,type="password",key=f"key_{_p}",label_visibility="collapsed",placeholder=f"{_l} key")
        if _new!=_cur: st.session_state.api_keys[_p]=_new

    if KEYS_STORE_AVAILABLE:
        with st.expander(f"🔐 {T('save_keys')}"):
            _pw=st.text_input(T("password"),type="password",key="save_pwd")
            if st.button(T("encrypt_save"),key="btn_save_keys"):
                if _pw and save_keys(st.session_state.api_keys,_pw): st.success("OK")
                elif not _pw: st.warning("Введи пароль")

    _sb_label(T("agent_token"),top=True)
    _tok=st.text_input("Ввод",value=st.session_state.agent_token,type="password",key="tok_input",label_visibility="collapsed",placeholder="--token")
    if _tok!=st.session_state.agent_token: st.session_state.agent_token=_tok

    _sb_label(T("tg_section"),top=True)
    if os.getenv("TG_BOT_TOKEN") and os.getenv("TG_CHAT_ID"):
        st.caption("✅ Загружено из .env")
    st.toggle(T("tg_enable"),value=st.session_state.tg_enabled,key="tg_toggle",
              on_change=lambda: st.session_state.update(tg_enabled=st.session_state.tg_toggle))
    if st.session_state.tg_enabled:
        _tt=st.text_input("Bot Token",value=st.session_state.tg_token,type="password",key="tg_tok")
        if _tt!=st.session_state.tg_token: st.session_state.tg_token=_tt
        _tc=st.text_input("Chat ID",value=st.session_state.tg_chat_id,key="tg_chat")
        if _tc!=st.session_state.tg_chat_id: st.session_state.tg_chat_id=_tc
        _cd=st.number_input(T("tg_cooldown"),1,1440,st.session_state.tg_cooldown_min,key="tg_cd")
        if _cd!=st.session_state.tg_cooldown_min: st.session_state.tg_cooldown_min=int(_cd)
        if st.button(T("tg_test"),key="btn_tg_test",use_container_width=True):
            ok,err=send_telegram(f"Тест — {datetime.now().strftime('%H:%M:%S')}\nСерверов: {len(st.session_state.servers_dict)}","info")
            if ok: st.success("✅ Отправлено!")
            else: st.error(f"❌ {err}")
        st.caption(T("tg_hint"))

    _sb_label(T("export"),top=True)
    st.download_button(T("report_md"),data=build_report().encode(),
        file_name=f"ba_{datetime.now().strftime('%Y%m%d_%H%M')}.md",mime="text/markdown",
        use_container_width=True,key="dl_report")

    _sb_label(T("sysprompt"),top=True)
    st.session_state.system_prompt=st.text_area("Текст",value=st.session_state.system_prompt,height=60,label_visibility="collapsed")

    if has_session():
        _sb_label(T("session"),top=True)
        if st.button(T("forget"),key="btn_forget",use_container_width=True):
            clear_session(); st.success("Сессия удалена")

# ═══════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════
_c=sum(1 for i in open_inc if i["severity"]=="critical")
_w=sum(1 for i in open_inc if i["severity"]=="warning")
_badges=""
if _c: _badges+=f'<span class="inc-badge inc-critical">{_c} CRIT</span> '
if _w: _badges+=f'<span class="inc-badge inc-warning">{_w} WARN</span>'
st.markdown(f"""<div style="background:#150d24;border-bottom:1px solid #2a1a3d;padding:10px 20px;display:flex;align-items:center;justify-content:space-between">
  <div style="display:flex;align-items:center;gap:12px">
    <span style="font-size:13px;font-weight:600;color:#e6edf3">🕷️ BlackArachnia</span>
    <span style="font-size:11px;color:#6e7681">{env_choice} · {server_url}</span> {_badges}</div>
  <span style="font-size:11px;color:#6e7681">{datetime.now().strftime('%Y-%m-%d %H:%M')}</span></div>""", unsafe_allow_html=True)

tabs=st.tabs([T("tab_dashboard"),T("tab_overview"),T("tab_services"),T("tab_terminal"),
              T("tab_ai"),T("tab_incidents"),T("tab_logs"),T("tab_add")])
tab_dash,tab_ov,tab_svc,tab_term,tab_ai,tab_inc,tab_logs,tab_add=tabs

# ═══════════════════════════════════════════════════════════════
#  FRAGMENTS
# ═══════════════════════════════════════════════════════════════
@st.fragment(run_every=15)
def frag_live(): refresh_servers(); render_dashboard()
@st.fragment(run_every=None)
def frag_paused(): render_dashboard()

@st.fragment(run_every=15)
def frag_ov_live(): refresh_servers(); render_overview()
@st.fragment(run_every=None)
def frag_ov_paused(): render_overview()

# ── ДАШБОРД (все серверы сразу, фишка Grafana) ───────────────
def render_dashboard():
    servers=st.session_state.servers_dict
    online=sum(1 for n in servers if st.session_state.server_cache.get(n,{}).get("online"))
    total=len(servers)
    op=[i for i in st.session_state.incidents if i["status"]=="open"]

    m1,m2,m3=st.columns(3)
    m1.metric("Серверов",str(total))
    m2.metric("Онлайн",f"{online}/{total}")
    m3.metric("Инцидентов",str(len(op)))

    # Средняя нагрузка CPU/RAM/Disk по всем серверам с агентом
    def _avg(metric):
        vals=[st.session_state.server_cache.get(n,{}).get(metric) for n in servers]
        vals=[v for v in vals if v is not None]
        return sum(vals)/len(vals) if vals else None
    avg_cpu=_avg("cpu"); avg_ram=_avg("ram"); avg_disk=_avg("disk")

    st.markdown("<div style='height:10px'></div>",unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin-bottom:8px">СРЕДНЯЯ НАГРУЗКА</div>',unsafe_allow_html=True)
    g1,g2,g3=st.columns(3)
    for col,label,val in [(g1,"CPU",avg_cpu),(g2,"RAM",avg_ram),(g3,"DISK",avg_disk)]:
        with col:
            if val is None:
                st.markdown(f'<div class="res-card gauge-card"><div class="gauge-empty"><div class="gauge-num">—</div></div><div class="gauge-label">{label}</div><div style="font-size:10px;color:#6e7681">нет агента</div></div>',unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="res-card gauge-card">{radial_gauge(val,label,_color(val))}</div>',unsafe_allow_html=True)

    # Карточки серверов
    for name,url in servers.items():
        s=st.session_state.server_cache.get(name)
        cls="pending" if not s else ("online" if s["online"] else "offline")
        dot="dot-yellow" if not s else ("dot-green" if s["online"] else "dot-red")
        if s and s["online"]:
            cpu=s.get("cpu"); ram=s.get("ram"); disk=s.get("disk")
            up=s.get("net_up",0); down=s.get("net_down",0)
            metr=""
            if cpu is not None:
                metr=(f'<div style="display:flex;gap:18px;margin-top:8px;font-family:JetBrains Mono;font-size:12px">'
                      f'<span style="color:{_color(cpu)}">CPU {cpu:.0f}%</span>'
                      f'<span style="color:{_color(ram)}">RAM {ram:.0f}%</span>'
                      f'<span style="color:{_color(disk or 0)}">Disk {disk or 0:.0f}%</span>'
                      f'<span style="color:#bf5fff">↑{up:.0f} ↓{down:.0f} КБ/с</span></div>')
            else:
                metr='<div style="font-size:11px;color:#6e7681;margin-top:6px">агент не подключён</div>'
            extra=f'http {s["status_code"]} · {s["ip"]} · SSL {s["ssl_days"]}д'
        else:
            metr=""; extra=s["message"][:50] if s else "ожидание проверки"
        st.markdown(f"""<div class="dash-card {cls}">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <div><span class="dot {dot}"></span><b style="color:#e6edf3;font-size:14px">{name}</b>
              <span style="color:#6e7681;font-size:12px;margin-left:8px">{url}</span></div>
            <span style="font-size:11px;color:#6e7681">{extra}</span></div>
          {metr}</div>""", unsafe_allow_html=True)

    st.caption(f"{'🟢 авто-обновление 15с' if st.session_state.monitoring_active else '⏸ пауза'} · {datetime.now().strftime('%H:%M:%S')}")

# ── ОБЗОР одного сервера ──────────────────────────────────────
def render_overview():
    env=st.session_state.get("main_select",list(st.session_state.servers_dict.keys())[0])
    url=st.session_state.servers_dict.get(env,"")
    s=st.session_state.server_cache.get(env)
    if s is None:
        with st.spinner("Подключение..."):
            s=check_server(url)
            if s["online"]: st.session_state.uptime_start[env]=time.time()
            st.session_state.server_cache[env]=s
            push_uptime(env,s["online"]); check_thresholds(env,s)
    # Аптайм: реальный из агента (server_uptime), иначе — с момента обнаружения
    if s.get("server_uptime") is not None:
        up = s["server_uptime"]; up_real = True
    else:
        up = time.time()-st.session_state.uptime_start.get(env,time.time()); up_real = False
    h=st.session_state.metrics_history.get(env,{"cpu":[],"ram":[],"disk":[]})
    upt=get_uptime_pct(env)

    m1,m2,m3,m4,m5=st.columns(5)
    m1.metric(T("status"),T("online").upper() if s["online"] else T("offline").upper())
    m2.metric(T("uptime"),fmt_uptime(up) if s["online"] else "—",
              delta=None if up_real else "с запуска")
    m3.metric(T("http"),str(s["status_code"]))
    m4.metric(T("ssl"),f"{s['ssl_days']}d" if s["online"] else "—",delta="⚠ скоро" if s.get("ssl_days",999)<config.SSL_WARN_DAYS else None)
    m5.metric(T("uptime90"),f"{upt:.1f}%" if upt is not None else "—")

    st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
    if s["online"]:
        st.markdown(f'<div style="padding:8px 14px;background:#0d2a1a;border:1px solid #238636;border-radius:6px;font-size:12px;color:#3fb950"><span class="dot dot-green"></span><b>{env}</b> {T("online").lower()} · {s["ip"]} · {s["last_seen"]}</div>',unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="padding:8px 14px;background:#2d0f0f;border:1px solid #da3633;border-radius:6px;font-size:12px;color:#ff7b72"><span class="dot dot-red"></span><b>{env}</b> {T("offline").lower()} · {s["message"][:70]}</div>',unsafe_allow_html=True)

    pv=f"{upt:.2f}%" if upt is not None else "нет данных"
    st.markdown(f'<div style="font-size:11px;color:#6e7681;margin:12px 0 4px">UPTIME 90 DAYS — {pv}</div>',unsafe_allow_html=True)
    st.markdown(uptime_grid(env),unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px;color:#6e7681;margin-bottom:12px">{T("legend")}</div>',unsafe_allow_html=True)

    if s["online"] and s.get("cpu") is not None:
        st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin-bottom:8px">{T("resources")}</div>',unsafe_allow_html=True)
        r1,r2,r3=st.columns(3)
        cpu=s.get("cpu",0); ram=s.get("ram",0); disk=s.get("disk",0)
        with r1:
            st.markdown(f'<div class="res-card"><div class="res-label">CPU · {s.get("cores","?")} cores</div><div class="res-value">{cpu:.1f}%</div>{bar(cpu,_color(cpu))}<div style="margin-top:8px">{sparkline(h["cpu"],_color(cpu))}</div></div>',unsafe_allow_html=True)
        with r2:
            rg=f'{s.get("ram_used",0):.1f}/{s.get("ram_total",0):.1f}GB'
            st.markdown(f'<div class="res-card"><div class="res-label">RAM</div><div class="res-value">{ram:.1f}%</div><div style="font-size:10px;color:#6e7681">{rg}</div>{bar(ram,_color(ram))}<div style="margin-top:8px">{sparkline(h["ram"],_color(ram))}</div></div>',unsafe_allow_html=True)
        with r3:
            dg=f'{s.get("disk_used",0):.0f}/{s.get("disk_total",0):.0f}GB'
            st.markdown(f'<div class="res-card"><div class="res-label">DISK</div><div class="res-value">{disk:.1f}%</div><div style="font-size:10px;color:#6e7681">{dg}</div>{bar(disk,_color(disk))}<div style="margin-top:8px">{sparkline(h["disk"],_color(disk))}</div></div>',unsafe_allow_html=True)

        # Сеть + load average
        st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin:14px 0 8px">{T("network")}</div>',unsafe_allow_html=True)
        n1,n2,n3=st.columns(3)
        n1.metric("↑ Upload",f"{s.get('net_up',0):.1f} КБ/с")
        n2.metric("↓ Download",f"{s.get('net_down',0):.1f} КБ/с")
        la=s.get("load",[0,0,0])
        n3.metric("Load avg",f"{la[0]:.2f}" if la else "—")
    elif s["online"]:
        st.markdown(f'<div style="font-size:12px;color:#6e7681;padding:10px 0">{T("no_agent")}</div>',unsafe_allow_html=True)

    st.caption(f"{'🟢 авто-обновление 15с' if st.session_state.monitoring_active else '⏸ пауза'} · {datetime.now().strftime('%H:%M:%S')}")

# ═══════════════════════════════════════════════════════════════
#  TAB: ДАШБОРД
# ═══════════════════════════════════════════════════════════════
with tab_dash:
    st.markdown("<div style='padding:16px 20px 0'>",unsafe_allow_html=True)
    if st.session_state.monitoring_active: frag_live()
    else: frag_paused()
    st.markdown("</div>",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB: ОБЗОР СЕРВЕРА
# ═══════════════════════════════════════════════════════════════
with tab_ov:
    st.markdown("<div style='padding:16px 20px 0'>",unsafe_allow_html=True)
    if st.session_state.monitoring_active: frag_ov_live()
    else: frag_ov_paused()
    st.markdown("</div>",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB: СЛУЖБЫ
# ═══════════════════════════════════════════════════════════════
with tab_svc:
    st.markdown("<div style='padding:16px 20px 0'>",unsafe_allow_html=True)
    tok=st.session_state.agent_token
    host=server_url.replace("https://","").replace("http://","").split("/")[0]
    port=st.session_state.agent_ports.get(env_choice,config.AGENT_DEFAULT_PORT)

    # Топ процессов (фишка Netdata)
    st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin-bottom:8px">{T("top_proc")}</div>',unsafe_allow_html=True)
    if st.button("🔄 Загрузить процессы",key="btn_procs"):
        data=fetch_agent(host,port,"/processes")
        st.session_state["procs"]=data.get("processes",[]) if data else []
        if not data: st.error("Агент не отвечает")
    if st.session_state.get("procs"):
        rows=[{"PID":str(p["pid"]),"Процесс":p["name"],"CPU %":f"{p['cpu']:.1f}","RAM %":f"{p['ram']:.1f}"}
              for p in st.session_state["procs"]]
        st.dataframe(rows,hide_index=True,width="stretch",
            column_config={c:st.column_config.TextColumn(c,disabled=True) for c in ["PID","Процесс","CPU %","RAM %"]})

    # ── ОС сервера: автоопределение из агента + ручной override ──
    srv_os   = st.session_state.server_cache.get(env_choice, {}).get("os")
    detected = platform_cmds.os_kind(srv_os)
    osc1,osc2=st.columns([1,3])
    with osc1: st.markdown('<div style="font-size:11px;color:#8b949e;padding-top:8px">ОС сервера:</div>',unsafe_allow_html=True)
    with osc2:
        os_sel=st.radio("ОС",["auto","linux","windows"],horizontal=True,key="svc_os_sel",label_visibility="collapsed")
    kind = detected if os_sel=="auto" else os_sel
    if kind=="unknown": kind="linux"   # нет агента → команды по умолчанию Linux
    _det_txt={"linux":"Linux","windows":"Windows","unknown":"не определена"}[detected]

    st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin:10px 0 8px;border-top:1px solid #2a1a3d;padding-top:12px">СЛУЖБЫ · режим {kind.upper()} <span style="color:#3d2459">(агент: {_det_txt})</span></div>',unsafe_allow_html=True)
    cf,cc=st.columns([2,3])
    with cf:
        if st.button(T("svc_refresh"),key="btn_svc"):
            res=exec_remote(host,platform_cmds.list_services_cmd(kind),port,tok)
            if res.get("error"): st.session_state["svc_err"]=res["error"]
            else:
                svcs=[]
                for l in res.get("stdout","").splitlines():
                    if l.strip():
                        pp=l.split()
                        svcs.append({"name":pp[0].replace(".service",""),"sub":pp[1] if len(pp)>1 else "?"})
                st.session_state["svc_list"]=svcs; st.session_state.pop("svc_err",None)
    with cc:
        _svc_ph="nginx, docker, postgresql..." if kind=="linux" else "Spooler, W3SVC, MSSQLSERVER..."
        custom=st.text_input("Ввод",placeholder=_svc_ph,key="custom_svc",label_visibility="collapsed")
    if st.session_state.get("svc_err"): st.error(st.session_state["svc_err"])

    def _svc(action,svc):
        cmd=platform_cmds.service_action_cmd(kind,action,svc)
        with st.spinner(f"{action} {svc}..."):
            res=exec_remote(host,cmd,port,tok)
        out=res.get("stdout","").strip() if not res.get("error") else res["error"]
        st.session_state[f"svcres_{svc}"]=f"{action}: {out}"
        add_audit(env_choice,cmd,res.get("returncode",-1)); add_log(f"[service] {action} {svc} ({kind})")

    if custom:
        st.markdown(f'<div style="font-size:11px;color:#8b949e;margin:8px 0 4px">Управление: <b style="color:#e6edf3">{custom}</b></div>',unsafe_allow_html=True)
        b1,b2,b3,b4,b5=st.columns(5)
        if b1.button("▶ Start",key="sst"): _svc("start",custom); st.rerun()
        if b2.button("⏹ Stop",key="ssp"): _svc("stop",custom); st.rerun()
        if b3.button("↺ Restart",key="srs"): _svc("restart",custom); st.rerun()
        if b4.button("⟳ Reload",key="srl"): _svc("reload",custom); st.rerun()
        if b5.button("📋 Status",key="sss"):
            res=exec_remote(host,platform_cmds.service_status_cmd(kind,custom),port,tok)
            st.session_state[f"svcres_{custom}"]=res.get("stdout","") or res.get("error",""); st.rerun()
        rk=f"svcres_{custom}"
        if rk in st.session_state:
            out=st.session_state[rk]
            col="#3fb950" if ("active" in out or "Running" in out) else "#f85149" if "failed" in out.lower() else "#e6edf3"
            st.markdown(f'<pre style="background:#0a0612;border:1px solid #2a1a3d;border-radius:6px;padding:10px;font-size:12px;color:{col};white-space:pre-wrap;max-height:200px;overflow-y:auto">{out}</pre>',unsafe_allow_html=True)

    if st.session_state.get("svc_list"):
        for svc in st.session_state["svc_list"]:
            ac="#3fb950" if svc["sub"]=="running" else "#e3b341"
            c1,c2,c3,c4=st.columns([3,1,1,1])
            c1.markdown(f'<div style="padding:4px 0;font-size:12px;color:#e6edf3"><span class="dot dot-green"></span>{svc["name"]} <span style="font-size:10px;color:{ac}">{svc["sub"]}</span></div>',unsafe_allow_html=True)
            if c2.button("▶",key=f"qs_{svc['name']}"): _svc("start",svc["name"]); st.rerun()
            if c3.button("⏹",key=f"qx_{svc['name']}"): _svc("stop",svc["name"]); st.rerun()
            if c4.button("↺",key=f"qr_{svc['name']}"): _svc("restart",svc["name"]); st.rerun()

    st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin:14px 0 8px;border-top:1px solid #2a1a3d;padding-top:12px">{T("log_stream")} · {kind.upper()}</div>',unsafe_allow_html=True)
    l1,l2,l3=st.columns([3,1,1])
    with l1: logsrc=st.text_input("Ввод",value=platform_cmds.default_log_source(kind),key=f"logsrc_{kind}",label_visibility="collapsed")
    with l2: loglines=st.number_input("Строк",10,500,50,10,key="loglines")
    with l3: getlog=st.button(T("log_get"),key="btn_log",use_container_width=True)
    if getlog:
        res=exec_remote(host,platform_cmds.fetch_log_cmd(kind,logsrc,loglines),port,tok)
        if res.get("error"): st.error(res["error"])
        else:
            out=res.get("stdout","").strip()
            add_log(f"[log] {kind} {loglines} {logsrc}")
            st.markdown(f'<pre style="background:#0a0612;border:1px solid #2a1a3d;border-radius:8px;padding:14px;font-size:11px;color:#8b949e;white-space:pre-wrap;max-height:400px;overflow-y:auto">{out or "(пусто)"}</pre>',unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB: ТЕРМИНАЛ
# ═══════════════════════════════════════════════════════════════
with tab_term:
    st.markdown("<div style='padding:16px 20px 0'>",unsafe_allow_html=True)
    tok=st.session_state.agent_token
    host=server_url.replace("https://","").replace("http://","").split("/")[0]
    port=st.session_state.agent_ports.get(env_choice,config.AGENT_DEFAULT_PORT)
    prefill=st.session_state.pop("term_prefill","")
    tc,tsn,tau=st.tabs([T("console"),T("snippets"),T("audit")])

    with tc:
        qc=[("top -bn1|head -16","📊 top"),("df -h","💾 disk"),("free -h","🧠 mem"),
            ("uptime","⏱ uptime"),("ps aux --sort=-%cpu|head -12","⚙ procs"),("journalctl -n 25 --no-pager","📋 journal")]
        cols=st.columns(6)
        for col,(cmd,lbl) in zip(cols,qc):
            if col.button(lbl,key=f"qc_{lbl}",use_container_width=True):
                with st.spinner(cmd[:30]): res=exec_remote(host,cmd,port,tok)
                st.session_state.term_history.append({"ts":datetime.now().strftime("%H:%M:%S"),"cmd":cmd,"res":res})
                add_audit(env_choice,cmd,res.get("returncode",-1)); st.rerun()
        if st.session_state.term_history:
            _,d2,d3=st.columns([4,1,1])
            txt="\n".join(f"[{e['ts']}] $ {e['cmd']}\n{e['res'].get('error','') or e['res'].get('stdout','')}\n" for e in st.session_state.term_history)
            d2.download_button(T("dl_txt"),data=txt.encode(),file_name=f"term_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",mime="text/plain",key="dl_term",use_container_width=True)
            if d3.button(T("clear"),key="clr_term",use_container_width=True): st.session_state.term_history=[]; st.rerun()
            parts=[]
            for e in st.session_state.term_history:
                ce=e["cmd"].replace("<","&lt;").replace(">","&gt;")
                if e["res"].get("error"): oe=e["res"]["error"].replace("<","&lt;").replace(">","&gt;"); oc="#ff7b72"
                else: oe=e["res"].get("stdout","").replace("<","&lt;").replace(">","&gt;"); oc="#e6edf3" if e["res"].get("returncode",0)==0 else "#e3b341"
                parts.append(f'<div style="margin-bottom:10px"><div style="font-size:11px;margin-bottom:2px"><span style="color:#6e7681">[{e["ts"]}]</span> <span style="color:#bc8cff">{host}</span> <span style="color:#6e7681">$</span> <span style="color:#e6edf3">{ce}</span></div><pre style="margin:0;padding:8px 12px;background:#0a0612;border-radius:4px;border-left:2px solid #2a1a3d;color:{oc};font-size:11px;white-space:pre-wrap;max-height:280px;overflow-y:auto">{oe.strip() or "(нет вывода)"}</pre></div>')
            st.markdown('<div style="background:#0a0612;border:1px solid #2a1a3d;border-radius:8px;padding:14px;max-height:440px;overflow-y:auto">'+"".join(parts)+'</div>',unsafe_allow_html=True)
        else:
            st.markdown('<div style="background:#0a0612;border:1px solid #2a1a3d;border-radius:8px;padding:40px;text-align:center"><div style="font-size:12px;color:#3d2459">🕷️ BlackArachnia Terminal</div></div>',unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
        i1,i2=st.columns([5,1])
        with i1: cmdin=st.text_input("Ввод",value=prefill,placeholder=T("cmd_ph"),key="term_cmd",label_visibility="collapsed")
        with i2: runb=st.button(T("run"),key="term_run",use_container_width=True)
        if runb and cmdin.strip():
            c=cmdin.strip(); hh=st.session_state.term_cmd_history
            if not hh or hh[-1]!=c: hh.append(c); st.session_state.term_cmd_history=hh[-100:]
            with st.spinner("..."): res=exec_remote(host,c,port,tok)
            st.session_state.term_history.append({"ts":datetime.now().strftime("%H:%M:%S"),"cmd":c,"res":res})
            add_audit(env_choice,c,res.get("returncode",-1)); st.rerun()
        if st.session_state.term_cmd_history:
            with st.expander(f"⌨ {T('history')} ({len(st.session_state.term_cmd_history)})"):
                for pc in reversed(st.session_state.term_cmd_history[-20:]):
                    h1,h2=st.columns([5,1]); h1.code(pc,language="bash")
                    if h2.button("▶",key=f"h_{hash(pc)}",use_container_width=True):
                        with st.spinner("..."): res=exec_remote(host,pc,port,tok)
                        st.session_state.term_history.append({"ts":datetime.now().strftime("%H:%M:%S"),"cmd":pc,"res":res}); st.rerun()

    with tsn:
        with st.expander(T("add_snippet")):
            sn=st.text_input(T("name"),key="sn_name"); sc=st.text_area(T("command"),key="sn_cmd",height=55)
            if st.button(T("save"),key="save_snip") and sn.strip() and sc.strip():
                st.session_state.term_snippets.append({"name":sn.strip(),"cmd":sc.strip()}); st.rerun()
        for i,sp in enumerate(st.session_state.term_snippets):
            s1,s2,s3=st.columns([2,4,1])
            s1.markdown(f'<div style="font-size:12px;color:#e6edf3;padding:4px 0">{sp["name"]}</div>',unsafe_allow_html=True)
            s2.code(sp["cmd"],language="bash")
            sx1,sx2=s3.columns(2)
            if sx1.button("▶",key=f"rs_{i}",use_container_width=True):
                with st.spinner(sp["name"]): res=exec_remote(host,sp["cmd"],port,tok)
                st.session_state.term_history.append({"ts":datetime.now().strftime("%H:%M:%S"),"cmd":sp["cmd"],"res":res})
                add_audit(env_choice,sp["cmd"],res.get("returncode",-1)); st.rerun()
            if sx2.button("🗑",key=f"ds_{i}",use_container_width=True): st.session_state.term_snippets.pop(i); st.rerun()

    with tau:
        if not st.session_state.audit_log: st.info("Аудит пуст")
        else:
            a1,a2=st.columns([1,1])
            tsv="\n".join(["Time\tServer\tCmd\tRC"]+[f"{a['ts']}\t{a['server']}\t{a['cmd']}\t{a['rc']}" for a in reversed(st.session_state.audit_log)])
            a1.download_button("💾 .tsv",data=tsv.encode(),file_name=f"audit_{datetime.now().strftime('%Y%m%d')}.tsv",mime="text/tab-separated-values",key="dl_audit",use_container_width=True)
            if a2.button(T("clear"),key="clr_audit",use_container_width=True):
                if STORAGE_AVAILABLE: storage.clear_audit()
                st.session_state.audit_log=[]; st.rerun()
            rows=[{"Время":a["ts"],"Сервер":a["server"],"Команда":a["cmd"][:50],"RC":str(a["rc"]),"OK":"✅" if a["rc"]==0 else "❌"} for a in reversed(st.session_state.audit_log[-100:])]
            st.dataframe(rows,hide_index=True,width="stretch",column_config={c:st.column_config.TextColumn(c,disabled=True) for c in ["Время","Сервер","Команда","RC","OK"]})
    st.markdown("</div>",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB: ИИ ЧАТ (с памятью)
# ═══════════════════════════════════════════════════════════════
with tab_ai:
    st.markdown("<div style='padding:16px 20px 0'>",unsafe_allow_html=True)
    a1,a2,a3=st.columns([3,1,1])
    with a1:
        mode=st.selectbox("Выбор",["auto","groq","gemini","openai"],
            format_func=lambda x:{"auto":"Auto Router","groq":"Groq","gemini":"Gemini Flash","openai":"GPT-4o mini"}[x],
            label_visibility="collapsed")
    with a2:
        if st.button(T("analyze"),key="btn_analyze",use_container_width=True):
            p="Проанализируй состояние серверов, выяви проблемы и риски. Для каждой: что не так, почему важно, что делать.\n\n"+build_context()
            st.session_state.chat_messages.append({"role":"user","content":"🔍 Анализ серверов"})
            with st.spinner(T("thinking")): r=route_and_call(p,"auto")
            if not r.get("error"): st.session_state.chat_messages.append({"role":"assistant","content":r["text"],"meta":f"{r['label']} · {r['latency']}ms"})
            st.rerun()
    with a3:
        if st.button(T("clear_chat"),key="clr_chat",use_container_width=True): st.session_state.chat_messages=[]; st.rerun()

    qa=[(T("q_cmd"),"Предложи bash-команду для диагностики производительности. Только команда и краткое объяснение."),
        (T("q_report"),"Краткий отчёт по использованию ресурсов серверов."),
        (T("q_sec"),"Проверь конфигурацию на типичные проблемы безопасности.")]
    qcols=st.columns(3)
    for col,(lbl,pr) in zip(qcols,qa):
        if col.button(lbl,key=f"qai_{lbl[:5]}",use_container_width=True):
            st.session_state.chat_messages.append({"role":"user","content":lbl})
            with st.spinner(T("thinking")): r=route_and_call(pr+"\n\n"+build_context(),mode)
            if not r.get("error"): st.session_state.chat_messages.append({"role":"assistant","content":r["text"],"meta":f"{r['label']} · {r['latency']}ms"})
            st.rerun()

    box=st.container(height=420)
    with box:
        if not st.session_state.chat_messages:
            st.markdown(f'<div style="text-align:center;padding:40px 0;color:#6e7681;font-size:12px">{T("chat_empty")}</div>',unsafe_allow_html=True)
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("meta"): st.caption(msg["meta"])
                if msg["role"]=="assistant" and "```" in msg["content"]:
                    for cb in re.findall(r"```(?:bash|sh)?\n(.*?)```",msg["content"],re.DOTALL):
                        cb=cb.strip()
                        if cb and st.button(T("send_term"),key=f"st_{hash(cb)}",help=cb[:60]):
                            st.session_state["term_prefill"]=cb; st.info("→ Terminal")

    if uin:=st.chat_input(T("chat_ph")):
        with st.spinner(T("thinking")): r=route_and_call(uin,mode)
        st.session_state.chat_messages.append({"role":"user","content":uin})
        if r.get("error"): st.session_state.chat_messages.append({"role":"assistant","content":r["error"]})
        else:
            meta=f"{r['label']} · {r['task']} · {r['latency']}ms · {r['inp']}↑{r['out']}↓"
            st.session_state.chat_messages.append({"role":"assistant","content":r["text"],"meta":meta})
        st.rerun()
    st.markdown("</div>",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB: ИНЦИДЕНТЫ
# ═══════════════════════════════════════════════════════════════
with tab_inc:
    st.markdown("<div style='padding:16px 20px 0'>",unsafe_allow_html=True)
    with st.expander(T("thresholds")):
        st.caption("Инцидент создаётся автоматически при превышении")
        for sn in st.session_state.servers_dict:
            th=st.session_state.thresholds.get(sn,dict(config.DEFAULT_THRESHOLDS))
            st.markdown(f'<div style="font-size:11px;color:#e6edf3;margin:6px 0 2px">{sn}</div>',unsafe_allow_html=True)
            t1,t2,t3=st.columns(3)
            th["cpu"]=t1.number_input("CPU %",50,100,th["cpu"],key=f"th_c_{sn}")
            th["ram"]=t2.number_input("RAM %",50,100,th["ram"],key=f"th_r_{sn}")
            th["disk"]=t3.number_input("Disk %",50,100,th["disk"],key=f"th_d_{sn}")
            st.session_state.thresholds[sn]=th
    alli=st.session_state.incidents
    opi=[i for i in alli if i["status"]=="open"]
    c1,c2,c3,c4=st.columns(4)
    c1.metric(T("inc_open"),str(len(opi)))
    c2.metric(T("inc_crit"),str(sum(1 for i in opi if i["severity"]=="critical")))
    c3.metric(T("inc_warn"),str(sum(1 for i in opi if i["severity"]=="warning")))
    c4.metric(T("inc_total"),str(len(alli)))
    st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
    f1,f2,f3=st.columns([2,2,1])
    fs=f1.selectbox("Выбор",["all","open","closed"],format_func=lambda x:{"all":"Все","open":"Открытые","closed":"Закрытые"}[x],key="if_s",label_visibility="collapsed")
    fv=f2.selectbox("Выбор",["all","critical","warning"],format_func=lambda x:{"all":"Все","critical":"Критичные","warning":"Warning"}[x],key="if_v",label_visibility="collapsed")
    if f3.button(T("clear_closed"),key="clr_closed",use_container_width=True):
        if STORAGE_AVAILABLE: storage.delete_closed_incidents()
        st.session_state.incidents=[i for i in alli if i["status"]!="closed"]; st.rerun()
    flt=[i for i in reversed(alli) if (fs=="all" or i["status"]==fs) and (fv=="all" or i["severity"]==fv)]
    if not flt: st.markdown(f'<div style="text-align:center;padding:30px;font-size:12px;color:#6e7681">{T("no_inc")}</div>',unsafe_allow_html=True)
    else:
        for inc in flt[:100]:
            bc="inc-critical" if inc["severity"]=="critical" else "inc-warning"
            sc="#3fb950" if inc["status"]=="closed" else "#f85149" if inc["severity"]=="critical" else "#e3b341"
            st.markdown(f'<div style="background:#150d24;border:1px solid #2a1a3d;border-radius:8px;padding:10px 14px;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between"><div style="display:flex;align-items:center;gap:10px"><span class="inc-badge {bc}">{inc["severity"].upper()}</span><div><div style="font-size:12px;color:#e6edf3;font-weight:500">{inc["server"]} — {inc["msg"]}</div><div style="font-size:10px;color:#6e7681;margin-top:2px">#{inc["id"]} · {inc["opened"]}{" · закрыт "+inc["closed"] if inc["closed"] else ""}</div></div></div><span style="font-size:11px;color:{sc}">{inc["status"]}</span></div>',unsafe_allow_html=True)
            if inc["status"]=="open":
                if st.button(f"{T('resolve')} #{inc['id']}",key=f"res_{inc['id']}"):
                    inc["status"]="closed"; inc["closed"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if STORAGE_AVAILABLE: storage.update_incident(inc["id"],"closed",inc["closed"])
                    add_log(f"[incident] закрыт #{inc['id']}"); st.rerun()
    st.markdown("</div>",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB: ЛОГИ
# ═══════════════════════════════════════════════════════════════
with tab_logs:
    st.markdown("<div style='padding:16px 20px 0'>",unsafe_allow_html=True)
    l1,l2=st.columns([4,1])
    with l1: lf=st.text_input("Ввод",placeholder=T("filter_ph"),key="log_filter",label_visibility="collapsed")
    with l2:
        if st.button(T("clear"),key="clr_logs",use_container_width=True): st.session_state.logs=["[info] очищено."]; st.rerun()
    ls=st.session_state.logs[::-1]
    if lf: ls=[l for l in ls if lf.lower() in l.lower()]
    st.caption(f"{T('total')}: {len(st.session_state.logs)} · {T('shown')}: {len(ls)}")
    st.code("\n".join(ls) if ls else "// пусто",language=None)
    st.markdown("</div>",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB: ДОБАВИТЬ СЕРВЕР
# ═══════════════════════════════════════════════════════════════
with tab_add:
    st.markdown("<div style='padding:16px 20px 0'>",unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin-bottom:12px">{T("add_title")}</div>',unsafe_allow_html=True)
    st.markdown('<div style="background:#150d24;border:1px solid #2a1a3d;border-radius:8px;padding:14px 18px;margin-bottom:16px;font-size:12px;color:#8b949e;line-height:1.7">Для CPU/RAM запусти <code style="color:#bf5fff">agent.py</code> на сервере, порт <b style="color:#e6edf3">9999</b>.</div>',unsafe_allow_html=True)
    i1,i2=st.columns(2)
    with i1:
        st.markdown("**1. Скопируй**"); st.code("scp agent.py user@server:~/",language="bash")
        st.markdown("**2. Установи**"); st.code("pip install psutil",language="bash")
    with i2:
        st.markdown("**3. Запусти с токеном**"); st.code("nohup python agent.py --token SECRET &",language="bash")
        st.markdown("**4. Проверь**"); st.code("curl http://server:9999/metrics",language="bash")
    with st.expander("⚙️ systemd автозапуск"):
        st.code("""[Unit]
Description=BlackArachnia Agent
After=network.target
[Service]
ExecStart=/usr/bin/python3 /home/user/agent.py --token SECRET
Restart=always
[Install]
WantedBy=multi-user.target""",language="ini")
    st.markdown('<div style="background:#2d0f0f;border:1px solid #5a2020;border-radius:8px;padding:12px 16px;margin-top:12px;font-size:12px;color:#ff9b94;line-height:1.6">🔒 <b>Безопасность:</b> агент работает по обычному HTTP — в недоверенной сети не выставляйте порт наружу. Заверните трафик в SSH-туннель (<code style="color:#ffd0cc">ssh -L 9999:localhost:9999 user@server</code>), WireGuard или TLS-reverse-proxy. Подробнее — SECURITY.md.</div>',unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin-bottom:8px">{T("srv_name").upper()}</div>',unsafe_allow_html=True)
    n1,n2,n3=st.columns([2,2,1])
    with n1: nn=st.text_input(T("srv_name"),placeholder="PROD",key="add_name")
    with n2: nh=st.text_input(T("srv_host"),placeholder="server.com",key="add_host")
    with n3: np=st.number_input(T("agent_port"),1,65535,config.AGENT_DEFAULT_PORT,key="add_port")
    b1,b2,_=st.columns([1,1,2])
    dt_test=b1.button(T("test_agent"),key="btn_test",use_container_width=True)
    dt_add=b2.button(T("add_server"),key="btn_add",use_container_width=True)
    if dt_test and nh.strip():
        h=nh.strip().replace("https://","").replace("http://","").split("/")[0]
        with st.spinner(f"Тест {h}:{np}..."): m=fetch_agent(h,int(np))
        if m:
            t1,t2,t3=st.columns(3)
            t1.metric("CPU",f"{m.get('cpu_percent','?')}%")
            t2.metric("RAM",f"{m.get('ram_used_gb',0):.1f}/{m.get('ram_total_gb',0):.1f}GB")
            t3.metric("Disk",f"{m.get('disk_percent','?')}%")
            st.success(f"✅ Агент отвечает {h}:{np}")
        else: st.error(f"❌ Агент не отвечает {h}:{np}")
    if dt_add:
        n=nn.strip(); h=nh.strip().replace("https://","").replace("http://","").split("/")[0]
        if not n: st.error("Введи имя")
        elif not h: st.error("Введи хост")
        elif n in st.session_state.servers_dict: st.error(f"'{n}' существует")
        else:
            ok,err=is_valid_hostname(h)
            if ok:
                st.session_state.servers_dict[n]=h
                if int(np)!=config.AGENT_DEFAULT_PORT: st.session_state.agent_ports[n]=int(np)
                # Сохраняем для Telegram-бота и между сессиями
                try:
                    with open(_JSON_PATH,"w",encoding="utf-8") as f:
                        json.dump(st.session_state.servers_dict,f,ensure_ascii=False,indent=2)
                    with open(os.path.join(_DIR,".agent_ports.json"),"w",encoding="utf-8") as f:
                        json.dump(st.session_state.agent_ports,f,ensure_ascii=False,indent=2)
                except Exception: pass
                add_log(f"[config] добавлен {n} → {h}")
                st.success(f"✅ '{n}' добавлен"); st.rerun()
            else: st.error(err)
    st.markdown("---")
    st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin-bottom:8px">{T("cur_servers")}</div>',unsafe_allow_html=True)
    rows=[]
    for sn,sh in st.session_state.servers_dict.items():
        sc=st.session_state.server_cache.get(sn)
        rows.append({"Имя":sn,"Хост":sh,"Порт":str(st.session_state.agent_ports.get(sn,config.AGENT_DEFAULT_PORT)),
            "Статус":"Online" if sc and sc.get("online") else "Offline" if sc else "Pending",
            "CPU":f"{sc['cpu']:.0f}%" if sc and sc.get("cpu") is not None else "—",
            "RAM":f"{sc['ram']:.0f}%" if sc and sc.get("ram") is not None else "—"})
    st.dataframe(rows,hide_index=True,width="stretch",column_config={c:st.column_config.TextColumn(c,disabled=True) for c in ["Имя","Хост","Порт","Статус","CPU","RAM"]})
    st.markdown("</div>",unsafe_allow_html=True)