# ─────────────────────────────────────────────────────────────
# tg_bot.py — Telegram-бот BlackArachnia (polling, без библиотек)
#
# Команды:
#   /start          — приветствие, список команд
#   /status         — статус всех серверов (онлайн/офлайн, CPU/RAM)
#   /metrics <имя>  — подробные метрики конкретного сервера
#   /incidents      — активные инциденты
#   /ai <вопрос>    — задать вопрос ИИ о серверах
#
# Запускается автоматически из run.py, если в .env заданы:
#   TG_BOT_TOKEN=...      (токен от @BotFather)
#   TG_ALLOWED_CHAT=...   (твой chat_id — кто может управлять, опционально)
# ─────────────────────────────────────────────────────────────
import os, json, time, urllib.request, urllib.error, socket, ssl
import datetime as dt
from datetime import datetime

import config

_DIR       = os.path.dirname(os.path.abspath(__file__))
_JSON_PATH = os.path.join(_DIR, "temp_servers.json")
_PORTS     = os.path.join(_DIR, ".agent_ports.json")

API = "https://api.telegram.org/bot{token}/{method}"


# ── Чтение конфигурации проекта ───────────────────────────────
def load_servers():
    try:
        with open(_JSON_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"ЛАТ": "luat.ru"}

def load_ports():
    try:
        with open(_PORTS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def load_env():
    env_path = os.path.join(_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())


# ── Проверка серверов (та же логика что в app.py) ─────────────
def check_server(url):
    host = url.replace("https://", "").replace("http://", "").split("/")[0]
    hdr  = {"User-Agent": "Mozilla/5.0"}
    for scheme in ("https", "http"):
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(f"{scheme}://{host}", headers=hdr), timeout=4)
            ssl_days = 0
            if scheme == "https":
                try:
                    ctx = ssl.create_default_context()
                    with socket.create_connection((host, 443), timeout=2) as sk:
                        with ctx.wrap_socket(sk, server_hostname=host) as ss:
                            exp = datetime.strptime(ss.getpeercert()["notAfter"],
                                                    "%b %d %H:%M:%S %Y %Z")
                            ssl_days = (exp - datetime.now(dt.UTC).replace(tzinfo=None)).days
                except Exception:
                    pass
            return {"online": True, "code": r.getcode(), "ssl_days": ssl_days, "host": host}
        except Exception:
            continue
    return {"online": False, "code": "—", "ssl_days": 0, "host": host}

def fetch_agent(host, port=config.AGENT_DEFAULT_PORT, path="/metrics"):
    try:
        req = urllib.request.Request(f"http://{host}:{port}{path}",
                                     headers={"User-Agent": "BA-bot"})
        with urllib.request.urlopen(req, timeout=2) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {}


# ── Telegram API ──────────────────────────────────────────────
def tg_call(token, method, **params):
    url = API.format(token=token, method=method)
    data = json.dumps(params).encode()
    try:
        req = urllib.request.Request(url, data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=35) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"[tg_bot] ошибка API: {e}")
        return {}

def send(token, chat_id, text):
    tg_call(token, "sendMessage", chat_id=chat_id, text=text)


# ── Обработчики команд ────────────────────────────────────────
def cmd_status():
    servers = load_servers()
    ports   = load_ports()
    lines   = ["📊 Статус серверов:\n"]
    for name, url in servers.items():
        s = check_server(url)
        if s["online"]:
            m = fetch_agent(s["host"], ports.get(name, config.AGENT_DEFAULT_PORT))
            if m:
                ci = f" · CPU {m.get('cpu_percent',0):.0f}% · RAM {m.get('ram_percent',0):.0f}%"
            else:
                ci = " · агент офлайн"
            ssl_w = f" ⚠️SSL {s['ssl_days']}д" if s["ssl_days"] < config.SSL_WARN_DAYS else ""
            lines.append(f"🟢 {name} — онлайн{ci}{ssl_w}")
        else:
            lines.append(f"🔴 {name} — ОФЛАЙН")
    return "\n".join(lines)

def cmd_metrics(arg):
    servers = load_servers()
    ports   = load_ports()
    if not arg:
        return "Укажи имя сервера: /metrics " + ", ".join(servers.keys())
    name = arg.strip()
    match = None
    for n in servers:
        if n.lower() == name.lower():
            match = n; break
    if not match:
        return f"Сервер «{name}» не найден. Доступны: {', '.join(servers.keys())}"
    s = check_server(servers[match])
    if not s["online"]:
        return f"🔴 {match} — офлайн"
    m = fetch_agent(s["host"], ports.get(match, config.AGENT_DEFAULT_PORT))
    if not m:
        return f"🟢 {match} онлайн, но агент не отвечает (CPU/RAM недоступны)"
    up_h = m.get("uptime_sec", 0) // 3600
    return (f"📈 {match} ({s['host']})\n\n"
            f"CPU: {m.get('cpu_percent',0):.1f}% ({m.get('cpu_cores','?')} ядер)\n"
            f"RAM: {m.get('ram_percent',0):.1f}% "
            f"({m.get('ram_used_gb',0):.1f}/{m.get('ram_total_gb',0):.1f} GB)\n"
            f"Disk: {m.get('disk_percent',0):.1f}% "
            f"({m.get('disk_used_gb',0):.0f}/{m.get('disk_total_gb',0):.0f} GB)\n"
            f"Сеть: ↑{m.get('net_up_kbps',0):.0f} ↓{m.get('net_down_kbps',0):.0f} КБ/с\n"
            f"Uptime: {up_h} ч\n"
            f"SSL: {s['ssl_days']} дн.")

def cmd_incidents():
    # Инциденты считаем на лету — превышение порогов и офлайн
    servers = load_servers()
    ports   = load_ports()
    issues  = []
    for name, url in servers.items():
        s = check_server(url)
        if not s["online"]:
            issues.append(f"🔴 {name}: сервер недоступен")
            continue
        if s["ssl_days"] < config.SSL_CRIT_DAYS:
            issues.append(f"🔴 {name}: SSL истекает через {s['ssl_days']} дн.")
        elif s["ssl_days"] < config.SSL_WARN_DAYS:
            issues.append(f"🟡 {name}: SSL истекает через {s['ssl_days']} дн.")
        m = fetch_agent(s["host"], ports.get(name, config.AGENT_DEFAULT_PORT))
        if m:
            th = config.DEFAULT_THRESHOLDS
            if m.get("cpu_percent", 0) >= th["cpu"]:
                issues.append(f"🟡 {name}: CPU {m['cpu_percent']:.0f}%")
            if m.get("ram_percent", 0) >= th["ram"]:
                issues.append(f"🟡 {name}: RAM {m['ram_percent']:.0f}%")
            if m.get("disk_percent", 0) >= th["disk"]:
                issues.append(f"🟡 {name}: Disk {m['disk_percent']:.0f}%")
    if not issues:
        return "✅ Активных инцидентов нет"
    return "⚠️ Активные инциденты:\n\n" + "\n".join(issues)

def cmd_ai(arg):
    if not arg:
        return "Задай вопрос: /ai почему сервер тормозит?"
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return "ИИ недоступен: не задан GROQ_API_KEY в .env"
    # Контекст серверов
    servers = load_servers()
    ports   = load_ports()
    ctx = ["Состояние серверов:"]
    for name, url in servers.items():
        s = check_server(url)
        if s["online"]:
            m = fetch_agent(s["host"], ports.get(name, config.AGENT_DEFAULT_PORT))
            ci = f" CPU={m.get('cpu_percent',0):.0f}% RAM={m.get('ram_percent',0):.0f}%" if m else ""
            ctx.append(f"- {name}: онлайн ssl={s['ssl_days']}д{ci}")
        else:
            ctx.append(f"- {name}: офлайн")
    try:
        from groq import Groq
        r = Groq(api_key=key).chat.completions.create(
            model="llama-3.3-70b-versatile", max_tokens=1024,
            messages=[
                {"role": "system", "content": "Ты ассистент мониторинга серверов. Отвечай кратко на русском.\n\n" + "\n".join(ctx)},
                {"role": "user", "content": arg},
            ])
        return "🤖 " + r.choices[0].message.content
    except Exception as e:
        return f"Ошибка ИИ: {e}"

HELP = (
    "🕷️ BlackArachnia Bot\n\n"
    "Команды:\n"
    "/status — статус всех серверов\n"
    "/metrics <имя> — метрики сервера\n"
    "/incidents — активные инциденты\n"
    "/ai <вопрос> — спросить ИИ\n"
)


def handle(text):
    text = text.strip()
    if text.startswith("/start") or text.startswith("/help"):
        return HELP
    if text.startswith("/status"):
        return cmd_status()
    if text.startswith("/metrics"):
        return cmd_metrics(text[len("/metrics"):].strip())
    if text.startswith("/incidents"):
        return cmd_incidents()
    if text.startswith("/ai"):
        return cmd_ai(text[len("/ai"):].strip())
    return "Неизвестная команда. /help — список команд"


# ── Главный цикл (polling) ────────────────────────────────────
def main():
    load_env()
    token   = os.environ.get("TG_BOT_TOKEN", "").strip()
    allowed = os.environ.get("TG_ALLOWED_CHAT", "").strip()
    if not token:
        print("[tg_bot] TG_BOT_TOKEN не задан — бот не запущен")
        return
    print("[tg_bot] 🤖 Telegram-бот запущен (polling)")
    offset = 0
    while True:
        try:
            resp = tg_call(token, "getUpdates", offset=offset, timeout=30)
            for upd in resp.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message", {})
                chat_id = str(msg.get("chat", {}).get("id", ""))
                text    = msg.get("text", "")
                if not text:
                    continue
                # Ограничение доступа (если задан TG_ALLOWED_CHAT)
                if allowed and chat_id != allowed:
                    send(token, chat_id, "⛔ Доступ запрещён")
                    continue
                try:
                    reply = handle(text)
                except Exception as e:
                    reply = f"Ошибка: {e}"
                send(token, chat_id, reply)
        except Exception as e:
            print(f"[tg_bot] ошибка цикла: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()