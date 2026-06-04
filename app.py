import streamlit as st
import time, re, json, os, urllib.request, urllib.error, socket, ssl
import datetime as dt
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

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
    from keys_store import save_keys, load_keys, keys_file_exists, delete_keys
    KEYS_STORE_AVAILABLE = True
except ImportError:
    KEYS_STORE_AVAILABLE = False

st.set_page_config(page_title="BlackArachnia", page_icon="🕷️",
                   layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════
#  ПУТИ + АВТОВХОД
# ═══════════════════════════════════════════════════════════════
_DIR          = os.path.dirname(os.path.abspath(__file__))
_JSON_PATH    = os.path.join(_DIR, "temp_servers.json")
_SESSION_FILE = os.path.join(_DIR, ".ba_session")

import hashlib, base64 as _b64

def _machine_key():
    import platform, getpass
    return hashlib.sha256(f"{platform.node()}-{getpass.getuser()}".encode()).digest()

def save_session(pwd):
    try:
        key = _machine_key()
        xored = bytes(p ^ key[i % 32] for i, p in enumerate(pwd.encode()))
        with open(_SESSION_FILE, "wb") as f:
            f.write(_b64.b64encode(xored))
    except Exception:
        pass

def load_session():
    try:
        if not os.path.exists(_SESSION_FILE):
            return ""
        key = _machine_key()
        with open(_SESSION_FILE, "rb") as f:
            xored = _b64.b64decode(f.read())
        return bytes(p ^ key[i % 32] for i, p in enumerate(xored)).decode("utf-8")
    except Exception:
        return ""

def clear_session():
    try:
        if os.path.exists(_SESSION_FILE):
            os.remove(_SESSION_FILE)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════
#  CSS — единая тёмная тема (GitHub Dark / Netdata)
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

*,*::before,*::after { box-sizing:border-box; }
[data-testid="stStatusWidget"],[data-testid="stDecoration"],
[data-testid="stToolbar"],header[data-testid="stHeader"],
#MainMenu,footer { display:none!important; }
.block-container { padding:0!important; max-width:100%!important; }
[data-testid="stAppViewContainer"] { padding:0!important; }

.stApp { background:#0a0612!important; color:#ede6f3!important;
         font-family:'Inter',system-ui,sans-serif!important; }

/* Sidebar — статичный, не сворачивается */
[data-testid="stSidebar"] {
    background:#120a1f!important; border-right:1px solid #2a1a3d!important;
    min-width:225px!important; max-width:225px!important; transform:none!important;
}
[data-testid="stSidebarCollapsedControl"] { display:none!important; }
[data-testid="stSidebar"] * { color:#8b949e!important; font-size:12px!important; }
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] .stNumberInput input {
    background:#0a0612!important; border:1px solid #3d2459!important;
    color:#e6edf3!important; font-size:12px!important; border-radius:6px!important; }
[data-testid="stSidebar"] .stSelectbox > div > div {
    background:#0a0612!important; border:1px solid #3d2459!important;
    color:#e6edf3!important; border-radius:6px!important; }
[data-testid="stSidebar"] .stButton > button {
    background:#2a1a3d!important; border:1px solid #3d2459!important;
    color:#8b949e!important; border-radius:6px!important; width:100%!important; }
[data-testid="stSidebar"] .stButton > button:hover {
    background:#3d2459!important; color:#e6edf3!important; }
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background:#0a0612!important; border:1px solid #2a1a3d!important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background:#150d24!important; border-bottom:1px solid #2a1a3d!important;
    gap:0!important; padding:0 16px!important; }
.stTabs [data-baseweb="tab"] {
    background:transparent!important; color:#8b949e!important;
    font-size:12px!important; font-weight:500!important; padding:10px 14px!important;
    border-radius:0!important; border-bottom:2px solid transparent!important;
    letter-spacing:0.02em!important; text-transform:uppercase!important; }
.stTabs [aria-selected="true"] {
    color:#bf5fff!important; border-bottom:2px solid #bf5fff!important;
    background:transparent!important; }

/* Метрики */
[data-testid="stMetric"] {
    background:#150d24!important; border:1px solid #2a1a3d!important;
    border-radius:8px!important; padding:14px 16px!important; }
[data-testid="stMetricLabel"] { color:#8b949e!important; font-size:10px!important;
    font-weight:500!important; letter-spacing:0.08em!important;
    text-transform:uppercase!important; }
[data-testid="stMetricValue"] { color:#e6edf3!important; font-size:20px!important;
    font-weight:600!important; font-family:'JetBrains Mono',monospace!important; }
[data-testid="stMetricDelta"] { font-size:11px!important; }

/* Кнопки */
.stButton > button { background:#2a1a3d!important; color:#8b949e!important;
    border:1px solid #3d2459!important; border-radius:6px!important;
    font-size:12px!important; font-weight:500!important; transition:all .15s!important; }
.stButton > button:hover { background:#3d2459!important; color:#e6edf3!important;
    border-color:#bf5fff!important; box-shadow:0 0 8px rgba(191,95,255,.4)!important; }

/* Inputs */
.stTextInput input,.stTextArea textarea {
    background:#150d24!important; color:#e6edf3!important;
    border:1px solid #3d2459!important; border-radius:6px!important;
    font-size:13px!important; }
.stTextInput input:focus,.stTextArea textarea:focus {
    border-color:#bf5fff!important; box-shadow:0 0 0 3px rgba(191,95,255,.25)!important; }
.stSelectbox > div > div { background:#150d24!important; border:1px solid #3d2459!important;
    color:#e6edf3!important; border-radius:6px!important; font-size:13px!important; }
.stNumberInput input { background:#150d24!important; color:#e6edf3!important;
    border:1px solid #3d2459!important; border-radius:6px!important; }

/* Alerts */
.stSuccess { background:#0d2a1a!important; border:1px solid #238636!important;
    border-radius:6px!important; color:#3fb950!important; }
.stError { background:#2d0f0f!important; border:1px solid #da3633!important;
    border-radius:6px!important; color:#ff7b72!important; }
.stInfo { background:#0c2233!important; border:1px solid #388bfd!important;
    border-radius:6px!important; color:#bf5fff!important; }
.stWarning { background:#2a1f00!important; border:1px solid #d29922!important;
    border-radius:6px!important; color:#e3b341!important; }
[data-testid="stAlert"] { font-size:12px!important; }

/* Expander / DataFrame / Chat / Code */
[data-testid="stExpander"] { background:#150d24!important;
    border:1px solid #2a1a3d!important; border-radius:8px!important; }
[data-testid="stExpander"] summary { color:#8b949e!important; font-size:12px!important; }
[data-testid="stDataFrame"] { border:1px solid #2a1a3d!important;
    border-radius:8px!important; overflow:hidden!important; background:#0a0612!important; }
[data-testid="stDataFrame"] * { background:#0a0612!important; color:#c9d1d9!important; }
[data-testid="stDataFrame"] th { background:#150d24!important; color:#8b949e!important;
    font-size:11px!important; text-transform:uppercase!important; }
[data-testid="stDataFrame"] td { background:#0a0612!important; color:#c9d1d9!important;
    font-size:12px!important; font-family:'JetBrains Mono',monospace!important; }
[data-testid="stChatInput"] { background:#150d24!important;
    border:1px solid #3d2459!important; border-radius:8px!important; }
[data-testid="stChatInput"] textarea { background:#150d24!important; color:#e6edf3!important; }
[data-testid="stChatMessage"] { background:#150d24!important;
    border:1px solid #2a1a3d!important; border-radius:8px!important; margin-bottom:6px!important; }
[data-testid="stChatMessage"] p { color:#c9d1d9!important; font-size:13px!important; }
.stCode,code,pre { background:#150d24!important; color:#e6edf3!important;
    border:1px solid #2a1a3d!important; border-radius:6px!important;
    font-size:12px!important; font-family:'JetBrains Mono',monospace!important; }
.stCaption { color:#6e7681!important; font-size:11px!important; }
.stToggle label { color:#8b949e!important; font-size:12px!important; }
hr { border-color:#2a1a3d!important; }


/* Анти-мигание при авто-обновлении фрагмента */
[data-testid="stAppViewContainer"] * { animation-duration:0s!important; }
.element-container { transition:none!important; }
[data-stale="true"], [data-stale="false"] {
    opacity:1!important; transition:none!important; filter:none!important;
}
[data-testid="stVerticalBlock"] { transition:none!important; }
/* Скрываем индикатор "running" вверху справа */
[data-testid="stStatusWidget"] { display:none!important; }
.stSpinner { display:none!important; }


/* ════ НЕОНОВЫЕ ЭФФЕКТЫ ════ */
/* Активная вкладка — свечение */
.stTabs [aria-selected="true"] {
    text-shadow:0 0 8px rgba(191,95,255,.8)!important;
}
/* Метрики — фиолетовая рамка со свечением */
[data-testid="stMetric"] {
    box-shadow:0 0 0 1px rgba(191,95,255,.15), 0 2px 12px rgba(191,95,255,.08)!important;
}
[data-testid="stMetricValue"] {
    color:#d9a6ff!important; text-shadow:0 0 10px rgba(191,95,255,.5)!important;
}
/* Кнопки при наведении — неоновый край */
.stButton > button:hover {
    box-shadow:0 0 12px rgba(191,95,255,.5)!important;
    text-shadow:0 0 6px rgba(191,95,255,.6)!important;
}
/* Заголовок в шапке — свечение */
.ba-glow { text-shadow:0 0 12px rgba(191,95,255,.7); }
/* Чат-инпут focus */
[data-testid="stChatInput"]:focus-within {
    box-shadow:0 0 14px rgba(191,95,255,.4)!important;
}
/* Скроллбары фиолетовые */
::-webkit-scrollbar { width:8px; height:8px; }
::-webkit-scrollbar-track { background:#0a0612; }
::-webkit-scrollbar-thumb { background:#3d2459; border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background:#bf5fff; }
/* Градиентная полоса сверху приложения */
.stApp::before {
    content:""; position:fixed; top:0; left:0; right:0; height:2px; z-index:99999;
    background:linear-gradient(90deg,transparent,#bf5fff,#7b2fde,#bf5fff,transparent);
    box-shadow:0 0 10px rgba(191,95,255,.6);
}


/* ════ УСИЛЕННЫЙ НЕОН ════ */
/* Sidebar — неоновая правая граница со свечением */
[data-testid="stSidebar"] {
    border-right:1px solid rgba(191,95,255,.35)!important;
    box-shadow:4px 0 24px rgba(191,95,255,.12)!important;
}
/* Все текстовые поля — неоновая обводка */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
.stSelectbox > div > div, [data-testid="stChatInput"] {
    border:1px solid rgba(191,95,255,.3)!important;
    box-shadow:inset 0 0 8px rgba(191,95,255,.06)!important;
    transition:all .2s ease!important;
}
.stTextInput input:hover, .stTextArea textarea:hover,
.stNumberInput input:hover, .stSelectbox > div > div:hover {
    border-color:rgba(191,95,255,.6)!important;
    box-shadow:0 0 10px rgba(191,95,255,.25)!important;
}
/* Кнопки — мягкая неоновая обводка постоянно */
.stButton > button {
    border:1px solid rgba(191,95,255,.25)!important;
    transition:all .2s ease!important;
}
/* Метрики — неоновая рамка + градиентный фон */
[data-testid="stMetric"] {
    background:linear-gradient(135deg, #150d24 0%, #1a0f2e 100%)!important;
    border:1px solid rgba(191,95,255,.3)!important;
    box-shadow:0 0 0 1px rgba(191,95,255,.1), 0 4px 20px rgba(191,95,255,.1)!important;
    transition:all .25s ease!important;
}
[data-testid="stMetric"]:hover {
    border-color:rgba(191,95,255,.55)!important;
    box-shadow:0 0 20px rgba(191,95,255,.25)!important;
    transform:translateY(-2px);
}
/* Карточки ресурсов и серверов — неоновая обводка */
.res-card, .dash-card {
    border:1px solid rgba(191,95,255,.25)!important;
    box-shadow:0 2px 16px rgba(191,95,255,.08)!important;
    transition:all .25s ease!important;
}
.res-card:hover, .dash-card:hover {
    border-color:rgba(191,95,255,.5)!important;
    box-shadow:0 0 18px rgba(191,95,255,.2)!important;
}
/* Экспандеры — неон */
[data-testid="stExpander"] {
    border:1px solid rgba(191,95,255,.25)!important;
    box-shadow:0 0 12px rgba(191,95,255,.06)!important;
}
/* Тоггл (включатель) — фиолетовый когда активен */
[data-testid="stSidebar"] [aria-checked="true"] {
    background:#bf5fff!important;
}
/* Chat-сообщения — лёгкая обводка */
[data-testid="stChatMessage"] {
    border:1px solid rgba(191,95,255,.2)!important;
    box-shadow:0 2px 12px rgba(191,95,255,.06)!important;
}
/* Логотип в шапке + sidebar — пульсация свечения */
@keyframes neon-pulse {
    0%,100% { text-shadow:0 0 8px rgba(191,95,255,.5); }
    50%     { text-shadow:0 0 16px rgba(191,95,255,.9), 0 0 24px rgba(191,95,255,.4); }
}
.ba-glow { animation:neon-pulse 3s ease-in-out infinite; }
/* Заголовки секций sidebar — фиолетовый акцент слева */
[data-testid="stSidebar"] .stButton > button:hover {
    background:rgba(191,95,255,.12)!important;
}


/* Фикс белых полей в sidebar (password reveal, кнопка глаза) */
[data-testid="stSidebar"] input { background:#0a0612!important; color:#ede6f3!important; }
[data-testid="stSidebar"] [data-testid="stTextInput"] > div,
[data-testid="stSidebar"] [data-testid="stTextInput"] > div > div {
    background:#0a0612!important; border-radius:6px!important;
}
[data-testid="stSidebar"] button[title="Show password text"],
[data-testid="stSidebar"] button[title="Hide password text"] {
    background:#0a0612!important; color:#bf5fff!important;
}
/* Кнопки RU/EN и активные — градиент при наведении */
[data-testid="stSidebar"] .stButton > button:active {
    background:linear-gradient(135deg, rgba(191,95,255,.3), rgba(123,47,222,.3))!important;
}

/* Прогресс-бар */
.nd-bar-wrap { height:4px; background:#2a1a3d; border-radius:2px; overflow:hidden; margin-top:3px; }
.nd-bar-fill { height:100%; border-radius:2px; box-shadow:0 0 8px currentColor; filter:brightness(1.1); }

/* Sparkline */
.spark-wrap { display:flex; align-items:flex-end; gap:1px; height:32px; }
.spark-bar  { width:3px; border-radius:1px; min-height:1px; }

/* Статус-dot */
.dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:5px; }
.dot-green  { background:#3fb950; box-shadow:0 0 6px #3fb950; }
.dot-red    { background:#f85149; box-shadow:0 0 6px #f85149; }
.dot-yellow { background:#e3b341; box-shadow:0 0 6px #e3b341; }

/* Uptime 90 дней */
.upt-grid { display:flex; gap:2px; flex-wrap:wrap; margin:6px 0; }
.upt-cell { width:10px; height:20px; border-radius:2px; }

/* Incident badge */
.inc-badge { display:inline-block; padding:2px 8px; border-radius:12px;
    font-size:10px; font-weight:600; letter-spacing:0.05em; }
.inc-critical { background:#2d0f0f; color:#ff7b72; border:1px solid #f85149; }
.inc-warning  { background:#2a1f00; color:#e3b341; border:1px solid #d29922; }
.inc-ok       { background:#0d2a1a; color:#3fb950; border:1px solid #238636; }

/* Карточка ресурса */
.res-card { background:#150d24; border:1px solid #2a1a3d; border-radius:8px; padding:12px 14px; }
.res-label { font-size:10px; color:#6e7681; letter-spacing:0.08em; text-transform:uppercase; }
.res-value { font-size:22px; font-weight:600; color:#e6edf3;
    font-family:'JetBrains Mono',monospace; margin:4px 0; }

/* Дашборд-карточка сервера */
.dash-card { background:#150d24; border:1px solid #2a1a3d; border-radius:10px;
    padding:14px 16px; margin-bottom:8px; }
.dash-card.online  { border-left:3px solid #3fb950; }
.dash-card.offline { border-left:3px solid #f85149; }
.dash-card.pending { border-left:3px solid #e3b341; }

/* Паутина */
.spider-wrap { position:fixed; top:0; right:0; width:160px; height:160px;
    pointer-events:none; z-index:9999; overflow:hidden; }
@keyframes spider-drop { 0%{top:8px} 100%{top:100px} }
.spider { position:absolute; font-size:16px; right:16px; filter:drop-shadow(0 0 6px #bf5fff);
    animation:spider-drop 4s ease-in-out infinite alternate; }
.spider-thread { position:absolute; top:0; right:26px; width:1px;
    background:linear-gradient(to bottom,#3d2459,transparent); height:110px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* ════════ НЕОН-GLASS PASS ════════ */
/* Aurora — как фиксированный фон самого .stApp (не перекрывает контент,
   не ломает скролл сайдбара) */
.stApp{
  background:
    radial-gradient(42vw 42vw at 10% 4%,  rgba(123,47,222,.30), transparent 60%),
    radial-gradient(48vw 48vw at 92% 96%, rgba(34,211,238,.15), transparent 62%),
    radial-gradient(34vw 34vw at 84% 6%,  rgba(191,95,255,.18), transparent 60%),
    #0a0612 !important;
  background-attachment:fixed !important;
}
/* Верхняя полоса — два акцента */
.stApp::before{background:linear-gradient(90deg,transparent,#bf5fff,#22d3ee,#bf5fff,transparent)!important;}

/* Стеклянные карточки (glassmorphism) */
[data-testid="stMetric"], .res-card, .dash-card{
  background:linear-gradient(135deg, rgba(26,15,46,.62), rgba(16,9,28,.62))!important;
  backdrop-filter:blur(14px) saturate(150%);-webkit-backdrop-filter:blur(14px) saturate(150%);
  border:1px solid rgba(191,95,255,.30)!important;
  box-shadow:0 10px 32px rgba(0,0,0,.38), 0 0 0 1px rgba(191,95,255,.07),
             inset 0 1px 0 rgba(255,255,255,.05)!important;
}
[data-testid="stMetric"]:hover, .res-card:hover, .dash-card:hover{
  border-color:rgba(34,211,238,.55)!important;
  box-shadow:0 14px 40px rgba(0,0,0,.45), 0 0 22px rgba(34,211,238,.18)!important;
}
[data-testid="stMetricValue"]{font-size:26px!important;
  background:linear-gradient(90deg,#d9a6ff,#22d3ee);-webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;text-shadow:none!important;}

/* Радиальные гейджи */
.gauge-card{display:flex;flex-direction:column;align-items:center;gap:6px;padding:14px 8px!important;}
.gauge{position:relative;display:flex;align-items:center;justify-content:center;}
.gauge svg{display:block;}
.gauge-label{font-size:10px;color:#8b949e;letter-spacing:.1em;text-transform:uppercase;}
.gauge-empty{width:104px;height:104px;border-radius:50%;border:8px solid #2a1a3d;
  display:flex;align-items:center;justify-content:center;}
.gauge-num{font-size:22px;color:#6e7681;font-family:'JetBrains Mono',monospace;}

/* Табы-пилюли с циан-подсветкой активной */
.stTabs [data-baseweb="tab"]{border-radius:8px 8px 0 0!important;}
.stTabs [aria-selected="true"]{
  background:linear-gradient(180deg, rgba(191,95,255,.14), transparent)!important;
  border-bottom:2px solid #22d3ee!important;color:#d9a6ff!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="spider-wrap">
  <svg style="position:absolute;top:0;right:0;width:160px;height:160px" viewBox="0 0 160 160">
    <line x1="160" y1="0" x2="0" y2="0" stroke="#bf5fff" stroke-width="0.5" opacity="0.5"/>
    <line x1="160" y1="0" x2="160" y2="160" stroke="#bf5fff" stroke-width="0.5" opacity="0.5"/>
    <line x1="160" y1="0" x2="30" y2="160" stroke="#bf5fff" stroke-width="0.4" opacity="0.3"/>
    <path d="M130 0 Q160 0 160 30" stroke="#bf5fff" stroke-width="0.5" fill="none" opacity="0.4"/>
    <path d="M90 0 Q160 0 160 70" stroke="#bf5fff" stroke-width="0.4" fill="none" opacity="0.3"/>
  </svg>
  <div class="spider-thread"></div>
  <div class="spider">🕷️</div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  I18N
# ═══════════════════════════════════════════════════════════════
TR = {
"ru": {
 "monitoring":"МОНИТОРИНГ","auto_refresh":"Авто-обновление (15с)","environment":"ОКРУЖЕНИЕ",
 "api_keys":"API КЛЮЧИ","agent_token":"ТОКЕН АГЕНТА","export":"ЭКСПОРТ","sysprompt":"СИСТЕМНЫЙ ПРОМПТ",
 "save_keys":"Сохранить ключи","encrypt_save":"Зашифровать и сохранить","password":"Пароль",
 "report_md":"📄 Отчёт .md","language":"ЯЗЫК","session":"СЕССИЯ","forget":"🚪 Забыть меня",
 "tg_section":"TELEGRAM","tg_enable":"Включить алерты","tg_test":"🔔 Тест",
 "tg_hint":"Токен у @BotFather, chat_id у @userinfobot. Напиши боту /start!",
 "tg_cooldown":"Кулдаун (мин)",
 "tab_dashboard":"Дашборд","tab_overview":"Сервер","tab_services":"Службы","tab_terminal":"Терминал",
 "tab_ai":"ИИ Чат","tab_incidents":"Инциденты","tab_logs":"Логи","tab_add":"Добавить",
 "status":"СТАТУС","uptime":"АПТАЙМ","http":"HTTP","ssl":"SSL","uptime90":"АПТАЙМ 90Д",
 "resources":"РЕСУРСЫ","network":"СЕТЬ","top_proc":"ТОП ПРОЦЕССОВ","all_servers":"ВСЕ СЕРВЕРЫ",
 "no_agent":"CPU/RAM — запусти agent.py на сервере","legend":"■ ≥99% · ■ ≥90% · ■ <90% · ■ нет данных",
 "online":"Онлайн","offline":"Офлайн","pending":"Ожидание",
 "console":"Консоль","snippets":"Сниппеты","audit":"Аудит","clear":"🗑 Очистить","run":"▶ Запуск",
 "cmd_ph":"$ команда...","history":"История","dl_txt":"💾 .txt","add_snippet":"➕ Добавить сниппет",
 "save":"Сохранить","name":"Название","command":"Команда",
 "analyze":"🔍 Анализ","clear_chat":"🗑 Очистить","chat_ph":"Спроси о серверах...",
 "chat_empty":"Начни диалог — ИИ знает состояние серверов и помнит контекст","send_term":"▶ В терминал",
 "thinking":"Думаю...","q_cmd":"💡 Команда","q_report":"📊 Отчёт","q_sec":"🛡 Безопасность",
 "inc_open":"Открытых","inc_crit":"Критичных","inc_warn":"Предупреждений","inc_total":"Всего",
 "thresholds":"⚙️ Пороги","no_inc":"Нет инцидентов","resolve":"✓ Закрыть","clear_closed":"🗑 Закрытые",
 "svc_title":"SYSTEMD СЛУЖБЫ","svc_refresh":"🔄 Обновить","log_stream":"СТРИМИНГ ЛОГОВ","log_get":"📡 Получить",
 "add_title":"ДОБАВИТЬ СЕРВЕР","test_agent":"🔍 Тест агента","add_server":"＋ Добавить",
 "cur_servers":"ТЕКУЩИЕ СЕРВЕРЫ","srv_name":"Имя","srv_host":"Хост / IP","agent_port":"Порт агента",
 "filter_ph":"Фильтр...","total":"Всего","shown":"Показано",
},
"en": {
 "monitoring":"MONITORING","auto_refresh":"Auto-refresh (15s)","environment":"ENVIRONMENT",
 "api_keys":"API KEYS","agent_token":"AGENT TOKEN","export":"EXPORT","sysprompt":"SYSTEM PROMPT",
 "save_keys":"Save keys","encrypt_save":"Encrypt & save","password":"Password",
 "report_md":"📄 Report .md","language":"LANGUAGE","session":"SESSION","forget":"🚪 Forget me",
 "tg_section":"TELEGRAM","tg_enable":"Enable alerts","tg_test":"🔔 Test",
 "tg_hint":"Token from @BotFather, chat_id from @userinfobot. Send /start to bot!",
 "tg_cooldown":"Cooldown (min)",
 "tab_dashboard":"Dashboard","tab_overview":"Server","tab_services":"Services","tab_terminal":"Terminal",
 "tab_ai":"AI Chat","tab_incidents":"Incidents","tab_logs":"Logs","tab_add":"Add",
 "status":"STATUS","uptime":"UPTIME","http":"HTTP","ssl":"SSL","uptime90":"UPTIME 90D",
 "resources":"RESOURCES","network":"NETWORK","top_proc":"TOP PROCESSES","all_servers":"ALL SERVERS",
 "no_agent":"CPU/RAM — run agent.py on server","legend":"■ ≥99% · ■ ≥90% · ■ <90% · ■ no data",
 "online":"Online","offline":"Offline","pending":"Pending",
 "console":"Console","snippets":"Snippets","audit":"Audit","clear":"🗑 Clear","run":"▶ Run",
 "cmd_ph":"$ command...","history":"History","dl_txt":"💾 .txt","add_snippet":"➕ Add snippet",
 "save":"Save","name":"Name","command":"Command",
 "analyze":"🔍 Analyze","clear_chat":"🗑 Clear","chat_ph":"Ask about servers...",
 "chat_empty":"Start chatting — AI knows server state and remembers context","send_term":"▶ To terminal",
 "thinking":"Thinking...","q_cmd":"💡 Command","q_report":"📊 Report","q_sec":"🛡 Security",
 "inc_open":"Open","inc_crit":"Critical","inc_warn":"Warning","inc_total":"Total",
 "thresholds":"⚙️ Thresholds","no_inc":"No incidents","resolve":"✓ Resolve","clear_closed":"🗑 Closed",
 "svc_title":"SYSTEMD SERVICES","svc_refresh":"🔄 Refresh","log_stream":"LOG STREAMING","log_get":"📡 Fetch",
 "add_title":"ADD SERVER","test_agent":"🔍 Test agent","add_server":"＋ Add",
 "cur_servers":"CURRENT SERVERS","srv_name":"Name","srv_host":"Host / IP","agent_port":"Agent port",
 "filter_ph":"Filter...","total":"Total","shown":"Shown",
},
}

def T(k):
    return TR.get(st.session_state.get("lang","ru"), TR["ru"]).get(k, k)

# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def load_keys_from_env():
    return {"groq":os.getenv("GROQ_API_KEY",""),"gemini":os.getenv("GEMINI_API_KEY",""),
            "openai":os.getenv("OPENAI_API_KEY","")}

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

def add_log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{ts}] {msg}")
    if len(st.session_state.logs) > 300:
        st.session_state.logs = st.session_state.logs[-300:]

def add_audit(server, cmd, rc):
    st.session_state.audit_log.append({"ts":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "server":server,"cmd":cmd,"rc":rc})
    if len(st.session_state.audit_log) > 500:
        st.session_state.audit_log = st.session_state.audit_log[-500:]

def _color(v):
    return "#3fb950" if v<60 else "#e3b341" if v<85 else "#f85149"

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
    cd   = st.session_state.get("tg_cooldown_min", 15) * 60
    if now - last < cd: return
    ok, err = send_telegram(f"{server} — {msg}", severity)
    if ok:
        st.session_state.tg_last_sent[key] = now
        add_log(f"[telegram] алерт: {server} — {msg[:40]}")
    else:
        add_log(f"[telegram] ошибка: {err}")

# ── Инциденты ─────────────────────────────────────────────────
def check_thresholds(name, s):
    th  = st.session_state.thresholds.get(name, {"cpu":85,"ram":90,"disk":90})
    inc = st.session_state.incidents
    def _open(key, sev, msg):
        for i in inc:
            if i["server"]==name and i["key"]==key and i["status"]=="open": return
        inc.append({"id":len(inc)+1,"server":name,"key":key,"severity":sev,"msg":msg,
            "opened":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"closed":None,"status":"open"})
        add_log(f"[incident] {sev.upper()} — {name}: {msg}")
        tg_alert(f"{name}_{key}", name, sev, msg)
    def _close(key):
        for i in inc:
            if i["server"]==name and i["key"]==key and i["status"]=="open":
                i["status"]="closed"; i["closed"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    if sd<14: _open("ssl","critical",f"SSL истекает через {sd} дн.")
    elif sd<30: _open("ssl","warning",f"SSL истекает через {sd} дн.")
    else: _close("ssl")
    if len(inc)>1000: st.session_state.incidents = inc[-1000:]

# ── Uptime 90 дней ────────────────────────────────────────────
def push_uptime(name, online):
    today = datetime.now().strftime("%Y-%m-%d")
    h = st.session_state.uptime_history.setdefault(name, {})
    d = h.get(today, {"checks":0,"up":0})
    d["checks"]+=1
    if online: d["up"]+=1
    h[today]=d

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

# ── Метрики sparkline ─────────────────────────────────────────
def push_metrics(name, cpu, ram, disk=None):
    h = st.session_state.metrics_history.setdefault(name, {"cpu":[],"ram":[],"disk":[]})
    for k,v in [("cpu",cpu),("ram",ram),("disk",disk)]:
        if v is not None:
            h[k].append(round(v,1)); h[k]=h[k][-60:]

def sparkline(values, color="#bf5fff", h=32):
    if not values: return '<span style="color:#6e7681;font-size:10px">—</span>'
    vals=values[-40:]
    mx=max(vals) if max(vals)>0 else 1
    n=len(vals); w=120
    step=w/max(1,n-1)
    pts=[(i*step, h-(v/mx*(h-3))-1.5) for i,v in enumerate(vals)]
    poly=" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)
    area=f"0,{h} "+poly+f" {w},{h}"
    last=vals[-1]; col=_color(last)
    uid=str(abs(hash((tuple(vals), color)))%99999)
    svg=(f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
         f'<defs><linearGradient id="sp{uid}" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="{col}" stop-opacity="0.5"/>'
         f'<stop offset="100%" stop-color="{col}" stop-opacity="0"/></linearGradient></defs>'
         f'<polygon points="{area}" fill="url(#sp{uid})"/>'
         f'<polyline points="{poly}" fill="none" stroke="{col}" stroke-width="1.6" '
         f'stroke-linejoin="round" style="filter:drop-shadow(0 0 3px {col})"/></svg>')
    return (f'<div style="display:flex;align-items:center;gap:8px">{svg}'
            f'<span style="font-size:11px;font-weight:600;color:{col};font-family:JetBrains Mono">{last:.0f}%</span></div>')

def bar(pct, color):
    return f'<div class="nd-bar-wrap"><div class="nd-bar-fill" style="width:{min(pct,100):.0f}%;background:{color}"></div></div>'

def radial_gauge(pct, label, color, size=108):
    """Радиальный гейдж (SVG-кольцо) с градиентом и свечением."""
    import math
    pct=max(0.0, min(100.0, float(pct)))
    r=42.0; circ=2*math.pi*r
    off=circ*(1-pct/100.0)
    uid=re.sub(r'\W','',label) or 'g'
    return (
        f'<div class="gauge">'
        f'<svg viewBox="0 0 100 100" width="{size}" height="{size}">'
        f'<defs><linearGradient id="gg{uid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{color}"/><stop offset="100%" stop-color="#22d3ee"/></linearGradient></defs>'
        f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="#2a1a3d" stroke-width="8"/>'
        f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="url(#gg{uid})" stroke-width="8" '
        f'stroke-linecap="round" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{off:.1f}" '
        f'transform="rotate(-90 50 50)" style="filter:drop-shadow(0 0 5px {color});'
        f'transition:stroke-dashoffset .6s ease"/>'
        f'<text x="50" y="50" text-anchor="middle" dominant-baseline="central" fill="#e6edf3" '
        f'font-size="21" font-family="JetBrains Mono,monospace" font-weight="600">{pct:.0f}</text>'
        f'</svg><div class="gauge-label">{label}</div></div>'
    )

# ── Проверка сервера ──────────────────────────────────────────
def check_server(url):
    host = url.replace("https://","").replace("http://","").split("/")[0]
    hdr  = {"User-Agent":"Mozilla/5.0"}
    for scheme in ("https","http"):
        try:
            r = urllib.request.urlopen(urllib.request.Request(f"{scheme}://{host}",headers=hdr), timeout=4)
            ssl_days=0
            if scheme=="https":
                try:
                    ctx=ssl.create_default_context()
                    with socket.create_connection((host,443),timeout=2) as sk:
                        with ctx.wrap_socket(sk,server_hostname=host) as ss:
                            exp=datetime.strptime(ss.getpeercert()["notAfter"],"%b %d %H:%M:%S %Y %Z")
                            ssl_days=(exp-datetime.now(dt.UTC).replace(tzinfo=None)).days
                except Exception: pass
            try: ip=socket.gethostbyname(host)
            except Exception: ip="—"
            return {"online":True,"status_code":r.getcode(),"ip":ip,"ssl_days":ssl_days,
                    "message":"OK","last_seen":datetime.now().strftime("%H:%M:%S")}
        except Exception: continue
    try:
        urllib.request.urlopen(urllib.request.Request(f"http://{host}",headers=hdr),timeout=4)
    except Exception as e: err=str(e)
    else: err="недоступен"
    return {"online":False,"status_code":"—","ip":"—","ssl_days":0,"message":err,"last_seen":"—"}

def fetch_agent(host, port=9999, path="/metrics"):
    try:
        req=urllib.request.Request(f"http://{host}:{port}{path}",headers={"User-Agent":"BA/3"})
        with urllib.request.urlopen(req,timeout=2) as r:
            return json.loads(r.read().decode())
    except Exception: return {}

def exec_remote(host, cmd, port=9999, token=""):
    try:
        payload=json.dumps({"cmd":cmd,"token":token}).encode()
        req=urllib.request.Request(f"http://{host}:{port}/exec",data=payload,
            headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=35) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try: return {"error":json.loads(e.read().decode()).get("error",str(e))}
        except Exception: return {"error":f"HTTP {e.code}"}
    except Exception as e: return {"error":str(e)}

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
    return name, r

def refresh_servers():
    # Серверы опрашиваются параллельно (сеть — самое медленное место).
    # Сетевые вызовы — в потоках, запись в session_state — только в основном потоке.
    items = list(st.session_state.servers_dict.items())
    if not items:
        return
    ports = {n: st.session_state.agent_ports.get(n, 9999) for n, _ in items}
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
        if r["online"] and not prev.get("online"):
            st.session_state.uptime_start[name] = time.time()
        if not r["online"]:
            st.session_state.uptime_start.pop(name, None)
        st.session_state.server_cache[name] = r
        push_metrics(name, r.get("cpu"), r.get("ram"), r.get("disk"))
        push_uptime(name, r["online"])
        check_thresholds(name, r)

# ═══════════════════════════════════════════════════════════════
#  LLM-РОУТЕР (с памятью диалога)
# ═══════════════════════════════════════════════════════════════
ROUTING = {
 "code":("groq","llama-3.3-70b-versatile","Groq/Llama70B"),   # mixtral-8x7b снят в Groq
 "reasoning":("groq","llama-3.3-70b-versatile","Groq/Llama70B"),
 "long":("gemini","gemini-2.0-flash","Gemini Flash"),
 "general":("groq","llama-3.3-70b-versatile","Groq/Llama70B"),
}

def classify(p):
    if len(p)>16000: return "long"
    if re.search(r"\b(код|code|python|sql|bash|функци|class)\b",p,re.I): return "code"
    if re.search(r"\b(почему|объясни|why|analyze|проанализир|сравни)\b",p,re.I): return "reasoning"
    return "general"

def build_context():
    cache=st.session_state.get("server_cache",{})
    if not cache: return ""
    lines=["СОСТОЯНИЕ СЕРВЕРОВ:"]
    for name,s in cache.items():
        url=st.session_state.servers_dict.get(name,"")
        if s["online"]:
            ci=f" CPU={s['cpu']:.0f}% RAM={s['ram']:.0f}% Disk={s.get('disk',0):.0f}%" if s.get("cpu") is not None else ""
            w=" SSL ИСТЕКАЕТ!" if s.get("ssl_days",999)<30 else ""
            lines.append(f"- {name}({url}): ОНЛАЙН http={s['status_code']} ip={s['ip']} ssl={s['ssl_days']}д{w}{ci}")
        else:
            lines.append(f"- {name}({url}): ОФЛАЙН {s['message'][:40]}")
    op=[i for i in st.session_state.incidents if i["status"]=="open"]
    if op:
        lines.append(f"\nИНЦИДЕНТЫ ({len(op)}):")
        for i in op[:5]: lines.append(f"  [{i['severity'].upper()}] {i['server']}: {i['msg']}")
    return "\n".join(lines)

def _msgs(sys, prompt, history):
    m=[{"role":"system","content":sys}]
    for h in history[-10:]:
        if h.get("role") in ("user","assistant") and h.get("content"):
            m.append({"role":h["role"],"content":h["content"]})
    m.append({"role":"user","content":prompt})
    return m

def route_and_call(prompt, mode, use_history=True):
    keys=st.session_state.get("api_keys",{})
    if mode=="auto":
        task=classify(prompt); provider,model,label=ROUTING[task]
    else:
        provider=mode
        if provider=="groq": task=classify(prompt); model=ROUTING.get(task,ROUTING["general"])[1]; label=f"Groq/{model[:14]}"
        elif provider=="gemini": model,label,task="gemini-2.0-flash","Gemini Flash","general"
        elif provider=="openai": model,label,task="gpt-4o-mini","GPT-4o mini","general"
        else: return {"error":f"Неизвестный провайдер {provider}"}
    key=keys.get(provider,"")
    if not key: return {"error":f"Ключ {provider.upper()} не задан"}
    base=st.session_state.get("system_prompt","You are a helpful assistant.")
    ctx=build_context()
    system=(base+"\n\n"+ctx+"\n\nИспользуй данные о серверах. Отвечай на русском.") if ctx else base
    history=st.session_state.get("chat_messages",[]) if use_history else []
    try:
        t0=time.time()
        if provider=="groq":
            from groq import Groq
            r=Groq(api_key=key).chat.completions.create(model=model,max_tokens=4096,messages=_msgs(system,prompt,history))
            text=r.choices[0].message.content; inp,out=r.usage.prompt_tokens,r.usage.completion_tokens
        elif provider=="gemini":
            import google.generativeai as genai
            genai.configure(api_key=key)
            gm=genai.GenerativeModel(model,system_instruction=system)
            gh=[{"role":"model" if h["role"]=="assistant" else "user","parts":[h["content"]]}
                for h in history[-10:] if h.get("content")]
            chat=gm.start_chat(history=gh); r=chat.send_message(prompt)
            text=r.text; inp,out=len(prompt)//4,len(text)//4
        elif provider=="openai":
            from openai import OpenAI
            r=OpenAI(api_key=key).chat.completions.create(model=model,max_tokens=4096,messages=_msgs(system,prompt,history))
            text=r.choices[0].message.content; inp,out=r.usage.prompt_tokens,r.usage.completion_tokens
        return {"text":text,"label":label,"task":task,"inp":inp,"out":out,
                "latency":int((time.time()-t0)*1000),"error":""}
    except Exception as e:
        return {"error":f"API: {e}"}

def build_report():
    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    L=[f"# BlackArachnia Report",f"**{now}**",""]
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
            remember=st.checkbox("Запомнить меня на этом устройстве",value=True,key="chk_remember")
            if st.button("Войти",key="btn_unlock",use_container_width=True):
                loaded=load_keys(pwd)
                if loaded is not None:
                    st.session_state.api_keys=loaded
                    st.session_state.keys_unlocked=True
                    if remember: save_session(pwd)
                    st.rerun()
                else: st.error("Неверный пароль")
            if st.button("Войти без ключей",key="btn_skip",use_container_width=True):
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
    ("tg_cooldown_min",15),("tg_last_sent",{}),
    ("system_prompt","Ты — ассистент мониторинга серверов BlackArachnia. Помогай кратко и по делу."),
    ("term_snippets",[
        {"name":"Disk","cmd":"df -h"},{"name":"Memory","cmd":"free -h"},
        {"name":"Top CPU","cmd":"ps aux --sort=-%cpu | head -12"},
        {"name":"Ports","cmd":"ss -tlnp"},{"name":"Nginx","cmd":"systemctl status nginx --no-pager -l"},
        {"name":"Docker","cmd":"docker ps"},{"name":"Journal","cmd":"journalctl -n 40 --no-pager"},
    ]),
]:
    if k not in st.session_state: st.session_state[k]=v

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

    if os.path.exists(_SESSION_FILE):
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
    m4.metric(T("ssl"),f"{s['ssl_days']}d" if s["online"] else "—",delta="⚠ скоро" if s.get("ssl_days",999)<30 else None)
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
    port=st.session_state.agent_ports.get(env_choice,9999)

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

    st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin:14px 0 8px;border-top:1px solid #2a1a3d;padding-top:12px">{T("svc_title")}</div>',unsafe_allow_html=True)
    cf,cc=st.columns([2,3])
    with cf:
        if st.button(T("svc_refresh"),key="btn_svc"):
            res=exec_remote(host,"systemctl list-units --type=service --state=running --no-pager --no-legend | awk '{print $1,$4}' | head -30",port,tok)
            if res.get("error"): st.session_state["svc_err"]=res["error"]
            else:
                svcs=[]
                for l in res.get("stdout","").splitlines():
                    if l.strip():
                        pp=l.split()
                        svcs.append({"name":pp[0].replace(".service",""),"sub":pp[1] if len(pp)>1 else "?"})
                st.session_state["svc_list"]=svcs; st.session_state.pop("svc_err",None)
    with cc:
        custom=st.text_input("Ввод",placeholder="nginx, docker, postgresql...",key="custom_svc",label_visibility="collapsed")
    if st.session_state.get("svc_err"): st.error(st.session_state["svc_err"])

    def _svc(action,svc):
        cmd=f"sudo systemctl {action} {svc}.service 2>&1; systemctl is-active {svc}.service"
        with st.spinner(f"{action} {svc}..."):
            res=exec_remote(host,cmd,port,tok)
        out=res.get("stdout","").strip() if not res.get("error") else res["error"]
        st.session_state[f"svcres_{svc}"]=f"{action}: {out}"
        add_audit(env_choice,cmd,res.get("returncode",-1)); add_log(f"[service] {action} {svc}")

    if custom:
        st.markdown(f'<div style="font-size:11px;color:#8b949e;margin:8px 0 4px">Управление: <b style="color:#e6edf3">{custom}</b></div>',unsafe_allow_html=True)
        b1,b2,b3,b4,b5=st.columns(5)
        if b1.button("▶ Start",key="sst"): _svc("start",custom); st.rerun()
        if b2.button("⏹ Stop",key="ssp"): _svc("stop",custom); st.rerun()
        if b3.button("↺ Restart",key="srs"): _svc("restart",custom); st.rerun()
        if b4.button("⟳ Reload",key="srl"): _svc("reload",custom); st.rerun()
        if b5.button("📋 Status",key="sss"):
            res=exec_remote(host,f"systemctl status {custom}.service --no-pager -l 2>&1",port,tok)
            st.session_state[f"svcres_{custom}"]=res.get("stdout","") or res.get("error",""); st.rerun()
        rk=f"svcres_{custom}"
        if rk in st.session_state:
            out=st.session_state[rk]
            col="#3fb950" if "active" in out else "#f85149" if "failed" in out.lower() else "#e6edf3"
            st.markdown(f'<pre style="background:#0a0612;border:1px solid #2a1a3d;border-radius:6px;padding:10px;font-size:12px;color:{col};white-space:pre-wrap;max-height:200px;overflow-y:auto">{out}</pre>',unsafe_allow_html=True)

    if st.session_state.get("svc_list"):
        for svc in st.session_state["svc_list"]:
            ac="#3fb950" if svc["sub"]=="running" else "#e3b341"
            c1,c2,c3,c4=st.columns([3,1,1,1])
            c1.markdown(f'<div style="padding:4px 0;font-size:12px;color:#e6edf3"><span class="dot dot-green"></span>{svc["name"]} <span style="font-size:10px;color:{ac}">{svc["sub"]}</span></div>',unsafe_allow_html=True)
            if c2.button("▶",key=f"qs_{svc['name']}"): _svc("start",svc["name"]); st.rerun()
            if c3.button("⏹",key=f"qx_{svc['name']}"): _svc("stop",svc["name"]); st.rerun()
            if c4.button("↺",key=f"qr_{svc['name']}"): _svc("restart",svc["name"]); st.rerun()

    st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin:14px 0 8px;border-top:1px solid #2a1a3d;padding-top:12px">{T("log_stream")}</div>',unsafe_allow_html=True)
    l1,l2,l3=st.columns([3,1,1])
    with l1: logsrc=st.text_input("Ввод",value="/var/log/syslog",key="logsrc",label_visibility="collapsed")
    with l2: loglines=st.number_input("Строк",10,500,50,10,key="loglines")
    with l3: getlog=st.button(T("log_get"),key="btn_log",use_container_width=True)
    if getlog:
        res=exec_remote(host,f"tail -n {loglines} {logsrc} 2>&1",port,tok)
        if res.get("error"): st.error(res["error"])
        else:
            out=res.get("stdout","").strip()
            add_log(f"[log] tail {loglines} {logsrc}")
            st.markdown(f'<pre style="background:#0a0612;border:1px solid #2a1a3d;border-radius:8px;padding:14px;font-size:11px;color:#8b949e;white-space:pre-wrap;max-height:400px;overflow-y:auto">{out or "(пусто)"}</pre>',unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB: ТЕРМИНАЛ
# ═══════════════════════════════════════════════════════════════
with tab_term:
    st.markdown("<div style='padding:16px 20px 0'>",unsafe_allow_html=True)
    tok=st.session_state.agent_token
    host=server_url.replace("https://","").replace("http://","").split("/")[0]
    port=st.session_state.agent_ports.get(env_choice,9999)
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
            if a2.button(T("clear"),key="clr_audit",use_container_width=True): st.session_state.audit_log=[]; st.rerun()
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
            th=st.session_state.thresholds.get(sn,{"cpu":85,"ram":90,"disk":90})
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
    st.markdown("---")
    st.markdown(f'<div style="font-size:10px;color:#6e7681;letter-spacing:0.08em;margin-bottom:8px">{T("srv_name").upper()}</div>',unsafe_allow_html=True)
    n1,n2,n3=st.columns([2,2,1])
    with n1: nn=st.text_input(T("srv_name"),placeholder="PROD",key="add_name")
    with n2: nh=st.text_input(T("srv_host"),placeholder="server.com",key="add_host")
    with n3: np=st.number_input(T("agent_port"),1,65535,9999,key="add_port")
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
                if int(np)!=9999: st.session_state.agent_ports[n]=int(np)
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
        rows.append({"Имя":sn,"Хост":sh,"Порт":str(st.session_state.agent_ports.get(sn,9999)),
            "Статус":"Online" if sc and sc.get("online") else "Offline" if sc else "Pending",
            "CPU":f"{sc['cpu']:.0f}%" if sc and sc.get("cpu") is not None else "—",
            "RAM":f"{sc['ram']:.0f}%" if sc and sc.get("ram") is not None else "—"})
    st.dataframe(rows,hide_index=True,width="stretch",column_config={c:st.column_config.TextColumn(c,disabled=True) for c in ["Имя","Хост","Порт","Статус","CPU","RAM"]})
    st.markdown("</div>",unsafe_allow_html=True)