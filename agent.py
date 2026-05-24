# ─────────────────────────────────────────────────────────────
# agent.py — запускается на целевом сервере
# Отдаёт реальные CPU/RAM по HTTP на порту 9999
#
# Установка на сервере:
#   pip install psutil
#   python agent.py
#
# Для автозапуска (Linux):
#   nohup python agent.py &
# ─────────────────────────────────────────────────────────────
import json
import psutil
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 9999

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            metrics = {
                "cpu_percent":  psutil.cpu_percent(interval=1),
                "ram_percent":  psutil.virtual_memory().percent,
                "ram_used_gb":  round(psutil.virtual_memory().used / 1024**3, 2),
                "ram_total_gb": round(psutil.virtual_memory().total / 1024**3, 2),
                "disk_percent": psutil.disk_usage("/").percent,
            }
            body = json.dumps(metrics).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass  # отключаем лишние логи

if __name__ == "__main__":
    print(f"[agent] запущен на порту {PORT}")
    HTTPServer(("0.0.0.0", PORT), MetricsHandler).serve_forever()