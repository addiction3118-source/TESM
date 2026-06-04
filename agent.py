# ─────────────────────────────────────────────────────────────
# agent.py — агент мониторинга BlackArachnia
# Эндпоинты:
#   GET  /metrics   → CPU/RAM/Disk/Network/Uptime
#   GET  /processes → топ процессов по CPU/RAM
#   GET  /ping      → проверка живости
#   POST /exec      → выполнить команду  { "cmd": "...", "token": "..." }
#
# Установка:  pip install psutil
# Запуск:     python agent.py --token YOUR_SECRET
# Фон:        nohup python agent.py --token SECRET &
# ─────────────────────────────────────────────────────────────
import json, sys, os, time, subprocess, hmac, psutil
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT  = 9999
_BOOT = psutil.boot_time()
_DISK_ROOT = "C:\\" if os.name == "nt" else "/"   # корень диска для метрик (кроссплатформенно)
_MAX_BODY  = 64 * 1024                              # лимит тела POST (защита от DoS)
_net_prev = {"t": time.time(), "sent": 0, "recv": 0}


def _get_token():
    args = sys.argv[1:]
    if "--token" in args:
        idx = args.index("--token")
        if idx + 1 < len(args):
            return args[idx + 1]
    return os.environ.get("AGENT_TOKEN", "")


AGENT_TOKEN = _get_token()

BLOCKED = ["rm -rf /", "mkfs", ":(){:|:&};:", "dd if=", "> /dev/sda",
           "chmod -R 777 /", "shutdown", "reboot", "halt", "poweroff",
           "init 0", "init 6"]


def is_blocked(cmd):
    low = cmd.strip().lower()
    return any(b in low for b in BLOCKED)


def get_network_speed():
    global _net_prev
    now = time.time()
    io  = psutil.net_io_counters()
    dt  = max(0.1, now - _net_prev["t"])
    up   = (io.bytes_sent - _net_prev["sent"]) / dt / 1024
    down = (io.bytes_recv - _net_prev["recv"]) / dt / 1024
    _net_prev = {"t": now, "sent": io.bytes_sent, "recv": io.bytes_recv}
    return round(max(0, up), 1), round(max(0, down), 1)


class AgentHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/metrics":
            up_kbps, down_kbps = get_network_speed()
            vm = psutil.virtual_memory()
            du = psutil.disk_usage(_DISK_ROOT)
            self._send_json({
                "cpu_percent":   psutil.cpu_percent(interval=0.5),
                "cpu_cores":     psutil.cpu_count(),
                "ram_percent":   vm.percent,
                "ram_used_gb":   round(vm.used / 1024**3, 2),
                "ram_total_gb":  round(vm.total / 1024**3, 2),
                "disk_percent":  du.percent,
                "disk_used_gb":  round(du.used / 1024**3, 1),
                "disk_total_gb": round(du.total / 1024**3, 1),
                "net_up_kbps":   up_kbps,
                "net_down_kbps": down_kbps,
                "uptime_sec":    int(time.time() - _BOOT),
                "load_avg":      list(os.getloadavg()) if hasattr(os, "getloadavg") else [0, 0, 0],
            })
        elif self.path == "/processes":
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    procs.append({
                        "pid":  p.info["pid"],
                        "name": (p.info["name"] or "?")[:24],
                        "cpu":  round(p.info["cpu_percent"] or 0, 1),
                        "ram":  round(p.info["memory_percent"] or 0, 1),
                    })
                except Exception:
                    continue
            procs.sort(key=lambda x: x["cpu"], reverse=True)
            self._send_json({"processes": procs[:15]})
        elif self.path == "/ping":
            self._send_json({"ok": True, "token_required": bool(AGENT_TOKEN)})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/exec":
            self._send_json({"error": "not found"}, 404); return
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0 or length > _MAX_BODY:
            self._send_json({"error": "invalid body size"}, 400); return
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._send_json({"error": "invalid json"}, 400); return
        # /exec ТРЕБУЕТ токен. Без заданного токена удалённое выполнение команд
        # отключено (раньше при пустом токене /exec был открыт для всех — это RCE).
        if not AGENT_TOKEN:
            self._send_json({"error": "/exec отключён: запустите агент с --token SECRET"}, 403); return
        # Сравнение токена в постоянном времени — защита от тайминг-атаки.
        if not hmac.compare_digest(str(body.get("token", "")), AGENT_TOKEN):
            self._send_json({"error": "unauthorized"}, 403); return
        cmd = body.get("cmd", "").strip()
        if not cmd:
            self._send_json({"error": "empty command"}, 400); return
        if is_blocked(cmd):
            self._send_json({"error": "команда заблокирована политикой безопасности"}, 403); return
        try:
            proc = subprocess.run(cmd, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=30, cwd=os.path.expanduser("~"))
            self._send_json({"stdout": proc.stdout.decode("utf-8", errors="replace"),
                             "returncode": proc.returncode, "cmd": cmd})
        except subprocess.TimeoutExpired:
            self._send_json({"error": "timeout: команда выполнялась более 30 сек"}, 408)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    if not AGENT_TOKEN:
        print("[agent] WARNING: токен не задан → /exec ОТКЛЮЧЁН. Для команд: python agent.py --token SECRET")
    else:
        print("[agent] token set, /exec protected")
    print(f"[agent] BlackArachnia agent on port {PORT}")
    HTTPServer(("0.0.0.0", PORT), AgentHandler).serve_forever()