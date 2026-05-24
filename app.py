import streamlit as st
import time
import re
import json
import os
import urllib.request
import socket
import ssl
import datetime as dt
from datetime import datetime

<<<<<<< HEAD
try:
    from keys_store import save_keys, load_keys, keys_file_exists, delete_keys
    KEYS_STORE_AVAILABLE = True
except ImportError:
    KEYS_STORE_AVAILABLE = False

st.set_page_config(page_title="TESM", page_icon="🖥️", layout="wide")

st.markdown("""
<style>
/* ── Базовый сброс ── */
.stApp { background-color: #f8fafc !important; opacity: 1 !important; }
.stApp * { transition: none !important; animation: none !important; }
[data-testid="stStatusWidget"],[data-testid="stDecoration"],[data-testid="stToolbar"] { display: none !important; }

/* ── Скрываем стандартный header ── */
header[data-testid="stHeader"] { display: none !important; }

/* ── Убираем паддинг страницы ── */
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"] { padding: 0 !important; }

/* ── Сайдбар ── */
[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 0.5px solid #1e293b !important;
    min-width: 240px !important;
    max-width: 240px !important;
}
[data-testid="stSidebar"] * { color: #94a3b8 !important; }
[data-testid="stSidebar"] label { color: #64748b !important; font-size: 12px !important; }
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextArea textarea {
    background: #1e293b !important;
    border-color: #334155 !important;
    color: #e2e8f0 !important;
    font-size: 12px !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #1e293b !important;
    border-color: #334155 !important;
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: #1e293b !important;
    border-color: #334155 !important;
    color: #94a3b8 !important;
    font-size: 12px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #64748b !important;
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: #1e293b !important;
    border-color: #334155 !important;
}
[data-testid="stSidebar"] .stSuccess { background: #0a1f12 !important; }

/* ── Основной контент ── */
.main .block-container { padding: 0 !important; }

/* ── Метрики ── */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 0.5px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 16px !important;
}
[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    font-family: system-ui !important;
}
[data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-size: 22px !important;
    font-weight: 500 !important;
    font-family: system-ui !important;
}
[data-testid="stMetricDelta"] { font-size: 11px !important; }

/* ── Кнопки ── */
.stButton > button {
    background: #ffffff !important;
    color: #475569 !important;
    border: 0.5px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 400 !important;
}
.stButton > button:hover { border-color: #94a3b8 !important; color: #0f172a !important; }

/* ── Вкладки ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 0.5px solid #e2e8f0 !important;
    gap: 0 !important;
    padding: 0 24px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #94a3b8 !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    border-radius: 0 !important;
    padding: 12px 20px !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #0f172a !important;
    border-bottom: 2px solid #0f172a !important;
    background: transparent !important;
}

/* ── Датафрейм ── */
[data-testid="stDataFrame"] {
    border: 0.5px solid #e2e8f0 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ── Инпуты ── */
.stTextArea textarea, .stTextInput input {
    background: #ffffff !important;
    color: #0f172a !important;
    border: 0.5px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #0f172a !important;
    box-shadow: none !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: #ffffff !important;
    border: 0.5px solid #e2e8f0 !important;
    border-radius: 8px !important;
    color: #0f172a !important;
    font-size: 13px !important;
}

/* ── Алерты ── */
.stSuccess { background: #f0fdf4 !important; border-left: 3px solid #22c55e !important; border-radius: 8px !important; color: #166534 !important; }
.stError   { background: #fef2f2 !important; border-left: 3px solid #ef4444 !important; border-radius: 8px !important; color: #991b1b !important; }
.stInfo    { background: #eff6ff !important; border-left: 3px solid #3b82f6 !important; border-radius: 8px !important; color: #1e40af !important; }
.stWarning { background: #fffbeb !important; border-left: 3px solid #f59e0b !important; border-radius: 8px !important; color: #92400e !important; }
[data-testid="stAlert"] { font-size: 13px !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 0.5px solid #e2e8f0 !important;
    border-radius: 8px !important;
}

/* ── Чат ── */
[data-testid="stChatInput"] {
    background: #ffffff !important;
    border: 0.5px solid #e2e8f0 !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"]:focus-within { border-color: #0f172a !important; }
[data-testid="stChatMessage"] {
    background: #ffffff !important;
    border: 0.5px solid #e2e8f0 !important;
    border-radius: 12px !important;
    margin-bottom: 8px !important;
}
[data-testid="stChatMessage"] p { color: #374151 !important; font-size: 14px !important; }

/* ── Код ── */
.stCode, code, pre {
    background: #f8fafc !important;
    color: #0f172a !important;
    border: 0.5px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-size: 12px !important;
}

/* ── Toggle ── */
.stToggle label { color: #475569 !important; font-size: 13px !important; }

/* ── Divider ── */
hr { border-color: #e2e8f0 !important; }

/* ── Caption ── */
.stCaption { color: #94a3b8 !important; font-size: 11px !important; }

/* ── Прогресс-бар ── */
.progress-track {
    height: 5px;
    background: #f1f5f9;
    border-radius: 3px;
    overflow: hidden;
    margin-top: 4px;
}
.progress-fill { height: 100%; border-radius: 3px; }

/* ── Dark mode поддержка ── */
@media (prefers-color-scheme: dark) {
    .stApp { background-color: #0f172a !important; }
    [data-testid="stMetric"] { background: #1e293b !important; border-color: #334155 !important; }
    [data-testid="stMetricLabel"] { color: #64748b !important; }
    [data-testid="stMetricValue"] { color: #f1f5f9 !important; }
    .stTabs [data-baseweb="tab-list"] { border-color: #334155 !important; }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; }
    .stTabs [aria-selected="true"] { color: #f1f5f9 !important; border-color: #f1f5f9 !important; }
    .stButton > button { background: #1e293b !important; color: #94a3b8 !important; border-color: #334155 !important; }
    .stButton > button:hover { color: #f1f5f9 !important; border-color: #64748b !important; }
    .stTextArea textarea, .stTextInput input { background: #1e293b !important; color: #f1f5f9 !important; border-color: #334155 !important; }
    .stSelectbox > div > div { background: #1e293b !important; border-color: #334155 !important; color: #f1f5f9 !important; }
    [data-testid="stExpander"] { background: #1e293b !important; border-color: #334155 !important; }
    [data-testid="stDataFrame"] { border-color: #334155 !important; }
    [data-testid="stChatMessage"] { background: #1e293b !important; border-color: #334155 !important; }
    [data-testid="stChatMessage"] p { color: #cbd5e1 !important; }
    [data-testid="stChatInput"] { background: #1e293b !important; border-color: #334155 !important; }
    [data-testid="stChatInput"]:focus-within { border-color: #94a3b8 !important; }
    .stCode, code, pre { background: #1e293b !important; color: #f1f5f9 !important; border-color: #334155 !important; }
    .progress-track { background: #334155; }
    hr { border-color: #334155 !important; }
}
</style>
""", unsafe_allow_html=True)

# ─── ПУТИ ────────────────────────────────────────────────────
_DIR       = os.path.dirname(os.path.abspath(__file__))
_ENV_PATH  = os.path.join(_DIR, ".env")
_JSON_PATH = os.path.join(_DIR, "temp_servers.json")

# ─── КЛЮЧИ ───────────────────────────────────────────────────
def load_keys_from_env() -> dict:
    """Загружает ключи только из переменных окружения — без записи в файл."""
    return {
        "groq":   os.getenv("GROQ_API_KEY",   ""),
        "gemini": os.getenv("GEMINI_API_KEY",  ""),
        "openai": os.getenv("OPENAI_API_KEY",  ""),
    }

# ─── МОНИТОРИНГ ──────────────────────────────────────────────
def is_valid_hostname(hostname):
    if not hostname or not hostname.strip(): return False, "Адрес не может быть пустым!"
    if not re.match(r"^[a-zA-Z0-9.\-]+$", hostname): return False, "Недопустимые символы!"
    if not re.search(r"\.", hostname): return False, "Неполный домен."
    return True, ""

def check_real_server(url):
    hostname = url.replace("https://","").replace("http://","").split("/")[0]
    try:
        req = urllib.request.Request("https://"+hostname, headers={"User-Agent":"Mozilla/5.0"})
        response = urllib.request.urlopen(req, timeout=3)
=======
# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(
    page_title="TESM - Панель Управления",
    page_icon="🖥️",
    layout="wide"
)

# --- ДИЗАЙН: Terminal Dark ---
st.markdown("""
<style>
/* ── Базовый фон и шрифты ── */
.stApp {
    background-color: #080b12 !important;
    opacity: 1 !important;
}
.stApp * {
    transition: none !important;
    animation: none !important;
}

/* ── Скрываем лишнее ── */
[data-testid="stStatusWidget"],
[data-testid="stDecoration"],
[data-testid="stToolbar"] { display: none !important; }

/* ── Сайдбар ── */
[data-testid="stSidebar"] {
    background-color: #0d1117 !important;
    border-right: 1px solid #1e2535 !important;
}
[data-testid="stSidebar"] * {
    color: #7c8db5 !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #a0aec0 !important;
    letter-spacing: 0.05em;
}

/* ── Заголовок страницы ── */
h1 { color: #e2e8f0 !important; font-family: monospace !important; letter-spacing: 0.04em !important; }
h2 { color: #a0aec0 !important; font-family: monospace !important; }
h3 { color: #7c8db5 !important; font-family: monospace !important; }
p, .stMarkdown p { color: #7c8db5 !important; }

/* ── Вкладки ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0d1117 !important;
    border-bottom: 1px solid #1e2535 !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #4a5580 !important;
    font-family: monospace !important;
    font-size: 13px !important;
    letter-spacing: 0.06em !important;
    border-radius: 0 !important;
    padding: 10px 20px !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: #22c55e !important;
    border-bottom: 2px solid #22c55e !important;
    background: #0d1117 !important;
}

/* ── Метрики ── */
[data-testid="stMetric"] {
    background: #0d1117 !important;
    border: 1px solid #1e2535 !important;
    border-radius: 8px !important;
    padding: 14px 16px !important;
}
[data-testid="stMetricLabel"] {
    color: #4a5580 !important;
    font-family: monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    color: #e2e8f0 !important;
    font-family: monospace !important;
    font-size: 22px !important;
}
[data-testid="stMetricDelta"] { font-family: monospace !important; font-size: 11px !important; }

/* ── Кнопки ── */
.stButton > button {
    background: #0d1117 !important;
    color: #7c8db5 !important;
    border: 1px solid #1e2535 !important;
    border-radius: 6px !important;
    font-family: monospace !important;
    font-size: 12px !important;
    letter-spacing: 0.04em !important;
}
.stButton > button:hover {
    border-color: #22c55e !important;
    color: #22c55e !important;
}

/* ── Инфо-блоки / success / error ── */
[data-testid="stAlert"] {
    background: #0d1117 !important;
    border-radius: 6px !important;
    font-family: monospace !important;
    font-size: 13px !important;
    border-left: 3px solid #22c55e !important;
}
div[data-baseweb="notification"] {
    background: #0d1117 !important;
}

/* ── Успех / ошибка ── */
.stSuccess {
    background: #0a1a0f !important;
    border-left: 3px solid #22c55e !important;
    color: #22c55e !important;
}
.stError {
    background: #1a0a0a !important;
    border-left: 3px solid #ef4444 !important;
    color: #ef4444 !important;
}
.stInfo {
    background: #0a0f1a !important;
    border-left: 3px solid #3b82f6 !important;
    color: #3b82f6 !important;
}
.stWarning {
    background: #1a140a !important;
    border-left: 3px solid #f59e0b !important;
    color: #f59e0b !important;
}

/* ── Таблица ── */
[data-testid="stDataFrame"] {
    background: #0d1117 !important;
    border: 1px solid #1e2535 !important;
    border-radius: 8px !important;
    font-family: monospace !important;
}
.dvn-scroller { background: #0d1117 !important; }

/* ── Инпуты и селекты ── */
.stTextInput input, .stSelectbox select {
    background: #0d1117 !important;
    color: #a0aec0 !important;
    border: 1px solid #1e2535 !important;
    font-family: monospace !important;
}
.stTextArea textarea {
    background: #0d1117 !important;
    color: #a0aec0 !important;
    border: 1px solid #1e2535 !important;
    font-family: monospace !important;
}

/* ── Toggle ── */
.stToggle label { color: #7c8db5 !important; font-family: monospace !important; }

/* ── Divider ── */
hr { border-color: #1e2535 !important; }

/* ── Код / логи ── */
.stCode, code, pre {
    background: #0d1117 !important;
    color: #22c55e !important;
    border: 1px solid #1e2535 !important;
    font-family: monospace !important;
}

/* ── Caption / подписи ── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #2d3a55 !important;
    font-family: monospace !important;
    font-size: 11px !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #0d1117 !important;
    border: 1px solid #1e2535 !important;
    border-radius: 6px !important;
}
[data-testid="stExpander"] summary {
    color: #4a5580 !important;
    font-family: monospace !important;
    font-size: 12px !important;
}

/* ── Spinner ── */
.stSpinner { color: #22c55e !important; }

/* ── Subheader ── */
.stApp .stMarkdown h2 { border-bottom: 1px solid #1e2535; padding-bottom: 6px; }
</style>
""", unsafe_allow_html=True)

# --- ФУНКЦИИ ---
def is_valid_hostname(hostname):
    if not hostname or not hostname.strip():
        return False, "Адрес не может быть пустым!"
    if not re.match(r"^[a-zA-Z0-9.\-]+$", hostname):
        return False, "Недопустимые символы в адресе!"
    if not re.search(r"\.", hostname):
        return False, "Неполный домен — добавьте точку (например: example.com)."
    return True, ""

def check_real_server(url):
    hostname = url.replace("https://", "").replace("http://", "").split("/")[0]
    full_url = "https://" + hostname
    try:
        req = urllib.request.Request(full_url, headers={"User-Agent": "Mozilla/5.0"})
        response = urllib.request.urlopen(req, timeout=3)

>>>>>>> fd1828cefb60b37a5ae36e7e78a13604633b9489
        ssl_days = 0
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=2) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
<<<<<<< HEAD
                    exp = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                    ssl_days = (exp - datetime.now(dt.UTC).replace(tzinfo=None)).days
        except Exception:
            pass
        return {"online":True,"status_code":response.getcode(),
                "ip":socket.gethostbyname(hostname),"ssl_days":ssl_days,
                "message":"OK","last_seen":datetime.now().strftime("%H:%M:%S")}
    except Exception as e:
        return {"online":False,"status_code":"—","ip":"—",
                "ssl_days":0,"message":str(e),"last_seen":"—"}

def fetch_agent_metrics(hostname, port=9999):
    try:
        req = urllib.request.Request(f"http://{hostname}:{port}/metrics",
                                     headers={"User-Agent":"TESM/1.0"})
        with urllib.request.urlopen(req, timeout=2) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {}

def add_log(message):
=======
                    ssl_expiry = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                    ssl_days = (ssl_expiry - datetime.now(dt.UTC).replace(tzinfo=None)).days
        except Exception:
            pass

        return {
            "online": True,
            "status_code": response.getcode(),
            "ip": socket.gethostbyname(hostname),
            "ssl_days": ssl_days,
            "message": "OK",
            "last_seen": datetime.now().strftime("%H:%M:%S"),
        }
    except Exception as e:
        return {
            "online": False,
            "status_code": "—",
            "ip": "—",
            "ssl_days": 0,
            "message": str(e),
            "last_seen": "—",
        }

def add_log(message: str):
>>>>>>> fd1828cefb60b37a5ae36e7e78a13604633b9489
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{ts}] {message}")
    if len(st.session_state.logs) > 200:
        st.session_state.logs = st.session_state.logs[-200:]

<<<<<<< HEAD
def format_uptime(s):
    if s < 60:    return f"{int(s)}s"
    elif s < 3600: return f"{int(s//60)}m {int(s%60)}s"
    else:          return f"{int(s//3600)}h {int((s%3600)//60)}m"

def _refresh_servers():
    for name, url in st.session_state.servers_dict.items():
        r = check_real_server(url)
        prev = st.session_state.server_cache.get(name, {})
        if r["online"] and not prev.get("online"):
            st.session_state.uptime_start[name] = time.time()
        if not r["online"]:
            st.session_state.uptime_start.pop(name, None)
        if r["online"]:
            hostname = url.replace("https://","").replace("http://","").split("/")[0]
            m = fetch_agent_metrics(hostname)
            r["cpu"]  = m.get("cpu_percent")
            r["ram"]  = m.get("ram_percent")
            r["ram_used"]  = m.get("ram_used_gb")
            r["ram_total"] = m.get("ram_total_gb")
            r["disk"] = m.get("disk_percent")
        st.session_state.server_cache[name] = r
        add_log(f"[monitor] {name} — {'online' if r['online'] else 'offline'}, http={r['status_code']}")

# ─── LLM РОУТЕР ──────────────────────────────────────────────
TASK_PATTERNS = {
    "code":        [r"\bкод\b",r"\b(python|javascript|sql|bash|html)\b",r"\b(функци|класс|debug|баг)\b"],
    "reasoning":   [r"\b(почему|объясни|проанализир|сравни|стратег)\b"],
    "translation": [r"\b(переведи|translate|перевод)\b"],
    "summary":     [r"\b(сократи|резюмир|summarize)\b"],
    "simple":      [r"\b(привет|что такое|расскаж)\b"],
}
ROUTING_MAP = {
    "code":         ("groq",  "mixtral-8x7b-32768",      "Groq / Mixtral"),
    "reasoning":    ("groq",  "llama-3.3-70b-versatile", "Groq / Llama 70B"),
    "long_context": ("gemini","gemini-2.0-flash",         "Gemini Flash"),
    "translation":  ("groq",  "llama-3.1-8b-instant",    "Groq / Llama 8B"),
    "summary":      ("groq",  "llama-3.1-8b-instant",    "Groq / Llama 8B"),
    "simple":       ("groq",  "llama-3.1-8b-instant",    "Groq / Llama 8B"),
    "general":      ("groq",  "llama-3.3-70b-versatile", "Groq / Llama 70B"),
}

def classify_prompt(prompt):
    if len(prompt) > 16000: return "long_context"
    for task, patterns in TASK_PATTERNS.items():
        for p in patterns:
            if re.search(p, prompt.lower(), re.IGNORECASE): return task
    return "general"

def call_groq(prompt, model, key, system):
    from groq import Groq
    r = Groq(api_key=key).chat.completions.create(
        model=model, max_tokens=4096,
        messages=[{"role":"system","content":system},{"role":"user","content":prompt}])
    return r.choices[0].message.content, r.usage.prompt_tokens, r.usage.completion_tokens

def call_gemini(prompt, model, key, system):
    import google.generativeai as genai
    genai.configure(api_key=key)
    r = genai.GenerativeModel(model, system_instruction=system).generate_content(prompt)
    return r.text, len(prompt)//4, len(r.text)//4

def call_openai(prompt, model, key, system):
    from openai import OpenAI
    r = OpenAI(api_key=key).chat.completions.create(
        model=model, max_tokens=4096,
        messages=[{"role":"system","content":system},{"role":"user","content":prompt}])
    return r.choices[0].message.content, r.usage.prompt_tokens, r.usage.completion_tokens

def build_server_context():
    cache = st.session_state.get("server_cache", {})
    if not cache: return ""
    lines = ["ТЕКУЩЕЕ СОСТОЯНИЕ СЕРВЕРОВ:"]
    for name, s in cache.items():
        url = st.session_state.servers_dict.get(name, "")
        up = time.time() - st.session_state.uptime_start.get(name, time.time())
        if s["online"]:
            warn = " SSL ИСТЕКАЕТ!" if s["ssl_days"] < 30 else ""
            cpu_info = f" | CPU {s['cpu']:.0f}% | RAM {s['ram']:.0f}%" if s.get("cpu") is not None else ""
            lines.append(f"- {name} ({url}): ОНЛАЙН | HTTP {s['status_code']} | IP {s['ip']} | SSL {s['ssl_days']} дн.{warn} | uptime {format_uptime(up)}{cpu_info}")
        else:
            lines.append(f"- {name} ({url}): ОФЛАЙН | ошибка: {s['message']}")
    return "\n".join(lines)

def route_and_call(prompt, mode):
    keys = st.session_state.get("api_keys", {})
    if mode == "auto":
        task = classify_prompt(prompt)
        provider, model, label = ROUTING_MAP[task]
    else:
        provider = mode
        if provider == "groq":
            task = classify_prompt(prompt)
            model = ROUTING_MAP.get(task, ROUTING_MAP["general"])[1]
            label = f"Groq / {model}"
        elif provider == "gemini": model,label,task = "gemini-2.0-flash","Gemini Flash","general"
        elif provider == "openai": model,label,task = "gpt-4o-mini","GPT-4o mini","general"
        else: return {"error": f"Неизвестный провайдер: {provider}"}
    key = keys.get(provider, "")
    if not key:
        return {"error": f"Ключ {provider.upper()}_API_KEY не задан — добавь в sidebar и сохрани"}
    base = st.session_state.get("system_prompt", "You are a helpful assistant.")
    ctx = build_server_context()
    system = (base+"\n\n"+ctx+"\n\nЕсли спрашивают о серверах — используй данные выше. "
              "Если сервер офлайн — предложи шаги диагностики. Отвечай на русском.") if ctx else base
    try:
        t0 = time.time()
        if provider == "groq":   text,inp,out = call_groq(prompt,model,key,system)
        elif provider == "gemini": text,inp,out = call_gemini(prompt,model,key,system)
        elif provider == "openai": text,inp,out = call_openai(prompt,model,key,system)
        return {"text":text,"label":label,"task":task,
                "inp":inp,"out":out,"latency":int((time.time()-t0)*1000),"error":""}
    except Exception as e:
        return {"error": f"Ошибка API: {e}"}

# ─── ИНИЦИАЛИЗАЦИЯ ────────────────────────────────────────────
# ─── ЭКРАН ВХОДА / ПАРОЛЬ ────────────────────────────────────
if "keys_unlocked" not in st.session_state:
    st.session_state.keys_unlocked = False
if "api_keys" not in st.session_state:
    st.session_state.api_keys = load_keys_from_env()

if KEYS_STORE_AVAILABLE and not st.session_state.keys_unlocked:
    if keys_file_exists():
        # Файл с ключами есть — просим пароль
        st.markdown("""
        <div style="max-width:360px;margin:80px auto;padding:32px;background:#1e293b;
                    border-radius:16px;border:0.5px solid #334155;text-align:center">
            <div style="font-size:18px;font-weight:500;color:#f1f5f9;margin-bottom:4px">TESM</div>
            <div style="font-size:12px;color:#64748b;margin-bottom:24px">Введи пароль для расшифровки ключей</div>
        </div>
        """, unsafe_allow_html=True)
        col_c = st.columns([1,2,1])[1]
        with col_c:
            pwd = st.text_input("Пароль:", type="password", key="unlock_pwd",
                                placeholder="Введи пароль...")
            if st.button("Войти", width="stretch", key="btn_unlock"):
                loaded = load_keys(pwd)
                if loaded is not None:
                    st.session_state.api_keys = loaded
                    st.session_state.keys_unlocked = True
                    st.rerun()
                else:
                    st.error("Неверный пароль")
            if st.button("Войти без ключей", width="stretch", key="btn_skip"):
                st.session_state.keys_unlocked = True
                st.rerun()
        st.stop()
    else:
        # Файла нет — сразу пускаем
        st.session_state.keys_unlocked = True

if "servers_dict" not in st.session_state:
    if os.path.exists(_JSON_PATH):
        with open(_JSON_PATH, encoding="utf-8") as f:
            loaded = json.load(f)
        st.session_state.servers_dict = loaded if loaded else {"ЛАТ": "luat.ru"}
    else:
        st.session_state.servers_dict = {"ЛАТ": "luat.ru"}

if "logs"              not in st.session_state: st.session_state.logs = ["[info] система готова."]
if "last_refresh"      not in st.session_state: st.session_state.last_refresh = 0.0
if "monitoring_active" not in st.session_state: st.session_state.monitoring_active = True
if "server_cache"      not in st.session_state: st.session_state.server_cache = {}
if "uptime_start"      not in st.session_state: st.session_state.uptime_start = {}
if "chat_messages"     not in st.session_state: st.session_state.chat_messages = []
if "system_prompt"     not in st.session_state: st.session_state.system_prompt = "You are a helpful assistant."
if "api_keys"          not in st.session_state: st.session_state.api_keys = load_keys_from_env()

REFRESH_INTERVAL = 3

# ─── SIDEBAR ─────────────────────────────────────────────────
with st.sidebar:
    # Логотип
    st.markdown("""
    <div style="padding:16px 0 12px;text-align:center;border-bottom:0.5px solid #1e293b;margin-bottom:8px">
        <div style="font-size:11px;font-weight:600;color:#f1f5f9;letter-spacing:0.1em">TESM</div>
        <div style="font-size:9px;color:#334155;margin-top:2px">v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    # Авто-обновление
    st.markdown('<div style="font-size:10px;color:#475569;letter-spacing:0.08em;margin-bottom:4px">МОНИТОРИНГ</div>', unsafe_allow_html=True)
    mon = st.toggle("Авто-обновление", value=st.session_state.monitoring_active, key="mon_toggle")
    if mon != st.session_state.monitoring_active:
        st.session_state.monitoring_active = mon
        st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Статус ключей
    st.markdown('<div style="font-size:10px;color:#475569;letter-spacing:0.08em;margin:12px 0 6px">API КЛЮЧИ</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;color:#334155;padding:0 2px 8px">Ключи хранятся только в сессии браузера и не сохраняются на сервере</div>', unsafe_allow_html=True)

    for _p, _l in [("groq","Groq"),("gemini","Gemini"),("openai","OpenAI")]:
        _cur = st.session_state.api_keys.get(_p, "")
        _color = "#22c55e" if _cur else "#ef4444"
        _hint = "задан" if _cur else "не задан"
        st.markdown(
            f"<div style='display:flex;align-items:center;justify-content:space-between;padding:3px 2px'>"
            f"<div style='display:flex;align-items:center;gap:6px'>"
            f"<div style='width:6px;height:6px;border-radius:50%;background:{_color};flex-shrink:0'></div>"
            f"<span style='font-size:12px;color:#94a3b8'>{_l}</span></div>"
            f"<span style='font-size:10px;color:#475569'>{_hint}</span></div>",
            unsafe_allow_html=True
        )

    with st.expander("Ввести / сохранить ключи"):
        for _p, _l in [("groq","GROQ"),("gemini","GEMINI"),("openai","OPENAI")]:
            _new = st.text_input(
                f"{_l}_API_KEY:",
                value=st.session_state.api_keys.get(_p, ""),
                type="password",
                key=f"key_input_{_p}",
                placeholder=f"Вставь {_l}_API_KEY..."
            )
            if _new != st.session_state.api_keys.get(_p, ""):
                st.session_state.api_keys[_p] = _new

        if KEYS_STORE_AVAILABLE:
            st.caption("Сохранить зашифрованными на диск:")
            _pwd = st.text_input("Пароль для шифрования:", type="password",
                                 key="save_pwd", placeholder="Придумай пароль...")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Сохранить", key="btn_save_keys", width="stretch"):
                    if _pwd:
                        save_keys(st.session_state.api_keys, _pwd)
                        st.success("Сохранено!")
                    else:
                        st.error("Введи пароль")
            with col2:
                if st.button("Удалить файл", key="btn_del_keys",
                             width="stretch", type="secondary"):
                    delete_keys()
                    st.success("Удалено")
        else:
            st.caption("Ключи хранятся только до закрытия вкладки")

    # Выбор окружения
    st.markdown('<div style="font-size:10px;color:#475569;letter-spacing:0.08em;margin:12px 0 4px;border-top:0.5px solid #1e293b;padding-top:12px">ОКРУЖЕНИЕ</div>', unsafe_allow_html=True)
    env_choice = st.selectbox("", list(st.session_state.servers_dict.keys()),
                               key="main_select", label_visibility="collapsed")
    server_url = st.session_state.servers_dict[env_choice]

    with st.expander("Управление серверами"):
        n_name = st.text_input("Имя:", key="add_name")
        n_link = st.text_input("Домен:", key="add_link")
        if st.button("Добавить", key="btn_add", width="stretch"):
            is_ok, err = is_valid_hostname(n_link)
            if not n_name.strip(): st.error("Имя пусто!")
            elif n_name in st.session_state.servers_dict: st.error("Уже есть!")
            elif is_ok:
                st.session_state.servers_dict[n_name] = n_link
                add_log(f"[config] добавлен: {n_name} → {n_link}")
                st.rerun()
            else: st.error(err)
        if st.button("Удалить текущий", key="btn_del", type="secondary"):
            if len(st.session_state.servers_dict) > 1:
                del st.session_state.servers_dict[env_choice]
                st.session_state.server_cache.pop(env_choice, None)
                st.session_state.uptime_start.pop(env_choice, None)
                add_log(f"[config] удалён: {env_choice}")
                st.rerun()
            else: st.warning("Последний сервер!")

    # System prompt
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;color:#475569;letter-spacing:0.08em;margin:12px 0 4px;border-top:0.5px solid #1e293b;padding-top:12px">СИСТЕМНЫЙ ПРОМПТ</div>', unsafe_allow_html=True)
    st.session_state.system_prompt = st.text_area(
        "", value=st.session_state.system_prompt,
        height=70, label_visibility="collapsed", placeholder="Инструкция для ИИ...")

# ─── ЗАГОЛОВОК ───────────────────────────────────────────────
st.markdown(f"""
<div style="padding:20px 24px 0;display:flex;align-items:center;justify-content:space-between">
    <div>
        <div style="font-size:18px;font-weight:500;color:#0f172a">Server Management</div>
        <div style="font-size:12px;color:#94a3b8;margin-top:2px">{env_choice} · {server_url} · {datetime.now().strftime('%Y-%m-%d')}</div>
    </div>
    <div style="font-size:11px;color:#cbd5e1;background:#f1f5f9;padding:4px 12px;border-radius:20px;border:0.5px solid #e2e8f0">
        {'● live' if st.session_state.monitoring_active else '○ paused'}
    </div>
</div>
<hr style="margin:16px 24px 0;border-color:#e2e8f0">
""", unsafe_allow_html=True)

# ─── ВКЛАДКИ ─────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Monitor", "Manage", "AI Chat", "Logs"])

# ══ ФОНОВОЕ ОБНОВЛЕНИЕ ═══════════════════════════════════════
@st.fragment(run_every=3)
def _background_refresh():
    if st.session_state.get("monitoring_active", True):
        prev = str(st.session_state.server_cache)
        _refresh_servers()
        if str(st.session_state.server_cache) != prev:
            st.session_state["_data_updated"] = time.time()

def render_monitor():
    env = st.session_state.get("main_select", list(st.session_state.servers_dict.keys())[0])
    url = st.session_state.servers_dict.get(env, "")
    status = st.session_state.server_cache.get(env)
    if status is None:
        with st.spinner("Подключаемся..."):
            result = check_real_server(url)
            if result["online"]: st.session_state.uptime_start[env] = time.time()
            st.session_state.server_cache[env] = result
            status = result

    up = time.time() - st.session_state.uptime_start.get(env, time.time())

    # Метрики
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Uptime", format_uptime(up) if status["online"] else "—")
    ssl_d = ("⚠ скоро" if status["ssl_days"] < 30 else "✓ ok") if status["online"] else None
    col2.metric("SSL", f"{status['ssl_days']} дн." if status["online"] else "—", delta=ssl_d)
    col3.metric("Last seen", status.get("last_seen","—"))
    col4.metric("HTTP", str(status["status_code"]))

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if status["online"]:
        st.success(f"Online · {env} · {status['ip']}")
    else:
        st.error(f"Offline · {status['message']}")

    # CPU/RAM блок
    if status["online"] and status.get("cpu") is not None:
        st.markdown("---")
        st.markdown("**Системные ресурсы**")
        r1, r2, r3 = st.columns(3)
        cpu  = status.get("cpu", 0)
        ram  = status.get("ram", 0)
        disk = status.get("disk", 0)
        cpu_c  = "#22c55e" if cpu  < 60 else "#f59e0b" if cpu  < 85 else "#ef4444"
        ram_c  = "#22c55e" if ram  < 60 else "#f59e0b" if ram  < 85 else "#ef4444"
        disk_c = "#22c55e" if disk < 60 else "#f59e0b" if disk < 85 else "#ef4444"

        with r1:
            st.metric("CPU", f"{cpu:.1f}%")
            st.markdown(f'<div class="progress-track"><div class="progress-fill" style="width:{cpu}%;background:{cpu_c}"></div></div>', unsafe_allow_html=True)
        with r2:
            ram_gb = f"{status.get('ram_used',0):.1f}/{status.get('ram_total',0):.1f} GB"
            st.metric("RAM", ram_gb, delta=f"{ram:.0f}%")
            st.markdown(f'<div class="progress-track"><div class="progress-fill" style="width:{ram}%;background:{ram_c}"></div></div>', unsafe_allow_html=True)
        with r3:
            st.metric("Disk", f"{disk:.1f}%")
            st.markdown(f'<div class="progress-track"><div class="progress-fill" style="width:{disk}%;background:{disk_c}"></div></div>', unsafe_allow_html=True)
    elif status["online"]:
        st.caption("CPU/RAM недоступны — запусти agent.py на сервере")

    # Таблица всех серверов
    st.markdown("---")
    st.markdown("**Все серверы**")
    rows = []
    for name, srv_url in st.session_state.servers_dict.items():
        s = st.session_state.server_cache.get(name)
        up_s = time.time() - st.session_state.uptime_start.get(name, time.time())
        if s:
            rows.append({
                "Среда": name, "Хост": srv_url,
                "Статус": "Online" if s["online"] else "Offline",
                "Uptime": format_uptime(up_s) if s["online"] else "—",
                "CPU": f"{s['cpu']:.0f}%" if s.get("cpu") is not None else "—",
                "RAM": f"{s['ram']:.0f}%" if s.get("ram") is not None else "—",
                "SSL": s["ssl_days"] if s["online"] else "—",
                "Last seen": s.get("last_seen","—"),
                "HTTP": str(s["status_code"]),
            })
        else:
            rows.append({"Среда":name,"Хост":srv_url,"Статус":"Pending",
                         "Uptime":"—","CPU":"—","RAM":"—","SSL":"—","Last seen":"—","HTTP":"—"})
    st.dataframe(rows, width="stretch", hide_index=True,
        column_config={c: st.column_config.TextColumn(c, disabled=True)
                       for c in ["Среда","Хост","Статус","Uptime","CPU","RAM","SSL","Last seen","HTTP"]})

# ══ ВКЛАДКА 1 ════════════════════════════════════════════════
with tab1:
    st.markdown("<div style='padding:20px 0 0'>", unsafe_allow_html=True)
    _background_refresh()
    render_monitor()
    st.markdown("</div>", unsafe_allow_html=True)

# ══ ВКЛАДКА 2 ════════════════════════════════════════════════
with tab2:
    st.markdown(f"**{env_choice}** · `{server_url}`")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Действия**")
        if st.button("Перезапустить службы", width="stretch", key="btn_restart"):
            with st.spinner("Перезапуск..."): time.sleep(1)
            add_log(f"[action] перезапуск: {env_choice}")
            st.success("Готово")
        if st.button("Очистить кэш", width="stretch", key="btn_cache"):
            with st.spinner("Очистка..."): time.sleep(0.5)
            add_log(f"[action] кэш очищен: {env_choice}")
            st.info("Готово")
        if st.button("Проверить сейчас", width="stretch", key="btn_check"):
            with st.spinner("Проверяем..."):
=======
def format_uptime(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)} сек"
    elif seconds < 3600:
        return f"{int(seconds // 60)} мин {int(seconds % 60)} сек"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h} ч {m} мин"

# --- ИНИЦИАЛИЗАЦИЯ ---
if "servers_dict" not in st.session_state:
    _json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_servers.json")
    if os.path.exists(_json_path):
        with open(_json_path, encoding="utf-8") as _f:
            _loaded = json.load(_f)
        st.session_state.servers_dict = _loaded if _loaded else {"ЛАТ": "luat.ru"}
    else:
        st.session_state.servers_dict = {"ЛАТ": "luat.ru", "Google": "google.com"}

if "logs" not in st.session_state:
    st.session_state.logs = ["[INFO] система готова к работе."]
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = 0.0
if "monitoring_active" not in st.session_state:
    st.session_state.monitoring_active = True
if "server_cache" not in st.session_state:
    st.session_state.server_cache = {}
if "uptime_start" not in st.session_state:
    st.session_state.uptime_start = {}

REFRESH_INTERVAL = 3

# --- ОБНОВЛЕНИЕ ДАННЫХ ---
now = time.time()
need_refresh = (
    st.session_state.monitoring_active
    and (now - st.session_state.last_refresh >= REFRESH_INTERVAL)
)

if need_refresh:
    st.session_state.last_refresh = now
    for name, url in st.session_state.servers_dict.items():
        result = check_real_server(url)
        prev = st.session_state.server_cache.get(name, {})
        if result["online"] and not prev.get("online"):
            st.session_state.uptime_start[name] = time.time()
        if not result["online"]:
            st.session_state.uptime_start.pop(name, None)
        st.session_state.server_cache[name] = result
        status_str = "online" if result["online"] else "offline"
        add_log(f"[monitor] {name} ({url}) — {status_str}, http={result['status_code']}")

# --- ЗАГОЛОВОК ---
st.title("⬛ TESM // server management")
st.caption(f"terminal v1.0 · {datetime.now().strftime('%Y-%m-%d')}")
st.divider()

# --- SIDEBAR ---
st.sidebar.markdown("### `// среды`")

env_choice = st.sidebar.selectbox(
    "активная среда:",
    list(st.session_state.servers_dict.keys()),
    key="main_select",
)
server_url = st.session_state.servers_dict[env_choice]
st.sidebar.code(f"host: {server_url}", language=None)

monitoring_toggle = st.sidebar.toggle(
    "авто-обновление [3s]", value=st.session_state.monitoring_active
)
if monitoring_toggle != st.session_state.monitoring_active:
    st.session_state.monitoring_active = monitoring_toggle
    st.rerun()

with st.sidebar.expander("+ добавить / удалить"):
    n_name = st.text_input("имя:")
    n_link = st.text_input("домен:")
    if st.button("добавить"):
        is_ok, err = is_valid_hostname(n_link)
        if not n_name.strip():
            st.error("имя не может быть пустым!")
        elif n_name in st.session_state.servers_dict:
            st.error(f"'{n_name}' уже существует!")
        elif n_link in st.session_state.servers_dict.values():
            existing = next(k for k, v in st.session_state.servers_dict.items() if v == n_link)
            st.error(f"хост уже добавлен как '{existing}'!")
        elif is_ok:
            st.session_state.servers_dict[n_name] = n_link
            add_log(f"[config] добавлен: {n_name} → {n_link}")
            st.rerun()
        else:
            st.error(err)

    if st.button("удалить текущий", type="secondary"):
        if len(st.session_state.servers_dict) > 1:
            del st.session_state.servers_dict[env_choice]
            st.session_state.server_cache.pop(env_choice, None)
            st.session_state.uptime_start.pop(env_choice, None)
            add_log(f"[config] удалён: {env_choice}")
            st.rerun()
        else:
            st.warning("нельзя удалить последний сервер!")

if st.session_state.monitoring_active:
    elapsed = time.time() - st.session_state.last_refresh
    remaining = max(0.0, REFRESH_INTERVAL - elapsed)
    st.sidebar.caption(f"// next refresh in {remaining:.0f}s")

# --- ВКЛАДКИ ---
tab1, tab2, tab3 = st.tabs(["[ monitor ]", "[ manage ]", "[ logs ]"])

# ── ВКЛАДКА 1 ─────────────────────────────────────────────────────────────
with tab1:
    st.markdown(f"#### `{env_choice}` · `{server_url}`")

    status = st.session_state.server_cache.get(env_choice)
    if status is None:
        with st.spinner("connecting..."):
            result = check_real_server(server_url)
            if result["online"]:
                st.session_state.uptime_start[env_choice] = time.time()
            st.session_state.server_cache[env_choice] = result
            st.session_state.last_refresh = time.time()
            status = result

    uptime_sec = 0.0
    if env_choice in st.session_state.uptime_start:
        uptime_sec = time.time() - st.session_state.uptime_start[env_choice]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("UPTIME", format_uptime(uptime_sec) if status["online"] else "—")
    ssl_delta = None
    if status["online"]:
        ssl_delta = "⚠ expiring soon" if status["ssl_days"] < 30 else "✓ ok"
    col2.metric("SSL", f"{status['ssl_days']} days" if status["online"] else "—", delta=ssl_delta)
    col3.metric("LAST SEEN", status.get("last_seen", "—"))
    col4.metric("HTTP", str(status["status_code"]))

    if status["online"]:
        st.success(f"● ONLINE · {env_choice} · {status['ip']}")
    else:
        st.error(f"● OFFLINE · {status['message']}")

    st.divider()
    st.markdown("#### `// все серверы`")
    rows = []
    for name, url in st.session_state.servers_dict.items():
        s = st.session_state.server_cache.get(name)
        up_sec = 0.0
        if name in st.session_state.uptime_start:
            up_sec = time.time() - st.session_state.uptime_start[name]
        if s:
            rows.append({
                "среда": name, "хост": url,
                "статус": "● online" if s["online"] else "○ offline",
                "uptime": format_uptime(up_sec) if s["online"] else "—",
                "ssl, дн.": s["ssl_days"] if s["online"] else "—",
                "last seen": s.get("last_seen", "—"),
                "http": str(s["status_code"]),
            })
        else:
            rows.append({
                "среда": name, "хост": url, "статус": "~ pending",
                "uptime": "—", "ssl, дн.": "—", "last seen": "—", "http": "—",
            })
    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
        column_config={
            "среда":     st.column_config.TextColumn("среда",     disabled=True),
            "хост":      st.column_config.TextColumn("хост",      disabled=True),
            "статус":    st.column_config.TextColumn("статус",    disabled=True),
            "uptime":    st.column_config.TextColumn("uptime",    disabled=True),
            "ssl, дн.":  st.column_config.TextColumn("ssl, дн.", disabled=True),
            "last seen": st.column_config.TextColumn("last seen", disabled=True),
            "http":      st.column_config.TextColumn("http",      disabled=True),
        },
    )

# ── ВКЛАДКА 2 ─────────────────────────────────────────────────────────────
with tab2:
    st.markdown(f"#### `// управление · {env_choice}`")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**`actions`**")
        if st.button("▶ перезапустить службы", width="stretch"):
            with st.spinner("restarting..."):
                time.sleep(1)
            add_log(f"[action] перезапуск служб: {env_choice}")
            st.success("done.")

        if st.button("▶ очистить кэш", width="stretch"):
            with st.spinner("clearing..."):
                time.sleep(0.5)
            add_log(f"[action] кэш очищен: {env_choice}")
            st.info("done.")

        if st.button("▶ проверить сейчас", width="stretch"):
            with st.spinner("pinging..."):
>>>>>>> fd1828cefb60b37a5ae36e7e78a13604633b9489
                result = check_real_server(server_url)
                if result["online"] and env_choice not in st.session_state.uptime_start:
                    st.session_state.uptime_start[env_choice] = time.time()
                st.session_state.server_cache[env_choice] = result
            add_log(f"[manual] {env_choice}: {'online' if result['online'] else 'offline'}")
            st.rerun()
<<<<<<< HEAD
    with col_b:
        st.markdown("**Заметки**")
        nk = f"notes_{env_choice}"
        if nk not in st.session_state: st.session_state[nk] = ""
        note = st.text_area("", value=st.session_state[nk], height=140,
                            label_visibility="collapsed",
                            placeholder="Заметки к серверу...")
        if st.button("Сохранить", width="stretch", key="btn_note"):
            st.session_state[nk] = note
            add_log(f"[note] заметка обновлена: {env_choice}")
            st.success("Сохранено")


# ══ ВКЛАДКА 3 ════════════════════════════════════════════════
with tab3:
    col_mode, col_clear = st.columns([3, 1])
    with col_mode:
        chat_mode = st.selectbox("", ["auto","groq","gemini","openai"],
            format_func=lambda x: {
                "auto":   "Авто-роутер",
                "groq":   "Groq — бесплатно",
                "gemini": "Gemini Flash — бесплатно",
                "openai": "GPT-4o mini",
            }[x], label_visibility="collapsed")
    with col_clear:
        if st.button("Очистить чат", width="stretch", key="clear_chat"):
            st.session_state.chat_messages = []
            st.rerun()

    if not st.session_state.chat_messages:
        st.markdown("""
        <div style="text-align:center;padding:40px 0;color:#94a3b8;font-size:13px">
            Начни диалог — ИИ знает о состоянии твоих серверов
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("meta"):
                st.caption(msg["meta"])

    if user_input := st.chat_input("Задай вопрос..."):
        st.session_state.chat_messages.append({"role":"user","content":user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Думаю..."):
                result = route_and_call(user_input, chat_mode)
            if result.get("error"):
                st.error(result["error"])
                st.session_state.chat_messages.append({"role":"assistant","content":result["error"]})
            else:
                st.markdown(result["text"])
                meta = f"{result['label']} · {result['task']} · {result['latency']}ms · {result['inp']}↑ {result['out']}↓ tok"
                st.caption(meta)
                st.session_state.chat_messages.append({
                    "role":"assistant","content":result["text"],"meta":meta})

# ══ ВКЛАДКА 4 ════════════════════════════════════════════════
with tab4:
    col_l1, col_l2 = st.columns([3, 1])
    with col_l1:
        filter_text = st.text_input("", placeholder="Поиск по логу...",
                                    label_visibility="collapsed")
    with col_l2:
        if st.button("Очистить", width="stretch", key="clear_logs"):
            st.session_state.logs = ["[info] лог очищен."]
            st.rerun()
    logs = st.session_state.logs[::-1]
    if filter_text:
        logs = [l for l in logs if filter_text.lower() in l.lower()]
    st.caption(f"Всего: {len(st.session_state.logs)} · Показано: {len(logs)}")
    st.code("\n".join(logs) if logs else "// no entries.", language=None)
=======

    with col_b:
        st.markdown("**`notes`**")
        notes_key = f"notes_{env_choice}"
        if notes_key not in st.session_state:
            st.session_state[notes_key] = ""
        note = st.text_area(
            "заметки:",
            value=st.session_state[notes_key],
            height=150,
            label_visibility="collapsed",
            placeholder="// заметки к серверу..."
        )
        if st.button("▶ сохранить", width="stretch"):
            st.session_state[notes_key] = note
            add_log(f"[note] обновлена заметка: {env_choice}")
            st.success("saved.")

    st.divider()
    st.markdown("**`env vars`**")
    st.data_editor(
        {"var": ["ENV", "VERSION", "DEBUG"],
         "value": ["production", "1.0.0", "false"]},
        width="stretch", num_rows="dynamic",
    )

# ── ВКЛАДКА 3 ─────────────────────────────────────────────────────────────
with tab3:
    st.markdown("#### `// system log`")
    col_l1, col_l2 = st.columns([3, 1])
    with col_l1:
        filter_text = st.text_input("фильтр:", placeholder="// поиск по логу...")
    with col_l2:
        if st.button("▶ очистить", width="stretch"):
            st.session_state.logs = ["[info] лог очищен."]
            st.rerun()

    logs = st.session_state.logs[::-1]
    if filter_text:
        logs = [l for l in logs if filter_text.lower() in l.lower()]
    st.caption(f"// total: {len(st.session_state.logs)} · shown: {len(logs)}")
    st.code("\n".join(logs) if logs else "// no entries.", language=None)

# --- АВТО-RERUN ---
if st.session_state.monitoring_active:
    elapsed = time.time() - st.session_state.last_refresh
    remaining = max(0.5, REFRESH_INTERVAL - elapsed)
    time.sleep(remaining)
    st.rerun()
>>>>>>> fd1828cefb60b37a5ae36e7e78a13604633b9489
