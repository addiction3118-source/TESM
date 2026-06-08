# ─────────────────────────────────────────────────────────────
# storage.py — SQLite-персистентность состояния BlackArachnia
#
# Хранит то, что раньше жило только в st.session_state и терялось
# при перезапуске приложения:
#   - incidents  — инциденты (открытые/закрытые)
#   - metrics    — история метрик CPU/RAM/Disk (для спарклайнов)
#   - uptime     — аптайм по дням (сетка 90 дней)
#   - audit      — журнал выполненных команд
#
# Используется только стандартная библиотека (sqlite3) — без СУБД-сервера
# и без новых зависимостей, в духе проекта «без Docker/без СУБД».
# ─────────────────────────────────────────────────────────────
import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta

_DIR     = os.path.dirname(os.path.abspath(__file__))
_DB_PATH = os.path.join(_DIR, "blackarachnia.db")

# Одно соединение на процесс. Streamlit перезапускает скрипт при каждом
# взаимодействии, но импортированный модуль (и _conn) переживает rerun.
# check_same_thread=False + _lock — на случай если Streamlit дёргает нас
# из разных потоков (фрагменты/сессии).
_lock = threading.Lock()
_conn = None

# Политика хранения (чистится при старте, чтобы БД не росла бесконечно)
_METRICS_KEEP_DAYS   = 7
_UPTIME_KEEP_DAYS    = 120
_AUDIT_KEEP_ROWS     = 2000
_INCIDENTS_KEEP_ROWS = 5000


def _connect():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA synchronous=NORMAL")
        _init_schema(_conn)
    return _conn


def _init_schema(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS incidents(
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        server   TEXT,
        key      TEXT,
        severity TEXT,
        msg      TEXT,
        opened   TEXT,
        closed   TEXT,
        status   TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_inc_open ON incidents(server, key, status);

    CREATE TABLE IF NOT EXISTS metrics(
        id     INTEGER PRIMARY KEY AUTOINCREMENT,
        server TEXT,
        ts     REAL,
        cpu    REAL,
        ram    REAL,
        disk   REAL
    );
    CREATE INDEX IF NOT EXISTS idx_metrics_srv ON metrics(server, ts);

    CREATE TABLE IF NOT EXISTS uptime(
        server TEXT,
        day    TEXT,
        checks INTEGER,
        up     INTEGER,
        PRIMARY KEY(server, day)
    );

    CREATE TABLE IF NOT EXISTS audit(
        id     INTEGER PRIMARY KEY AUTOINCREMENT,
        ts     TEXT,
        server TEXT,
        cmd    TEXT,
        rc     INTEGER
    );
    """)
    c.commit()


def _prune(c):
    """Чистка старых данных по политике хранения."""
    cutoff_m = time.time() - _METRICS_KEEP_DAYS * 86400
    c.execute("DELETE FROM metrics WHERE ts < ?", (cutoff_m,))
    cutoff_u = (datetime.now() - timedelta(days=_UPTIME_KEEP_DAYS)).strftime("%Y-%m-%d")
    c.execute("DELETE FROM uptime WHERE day < ?", (cutoff_u,))
    c.execute("DELETE FROM audit WHERE id NOT IN "
              "(SELECT id FROM audit ORDER BY id DESC LIMIT ?)", (_AUDIT_KEEP_ROWS,))
    c.execute("DELETE FROM incidents WHERE id NOT IN "
              "(SELECT id FROM incidents ORDER BY id DESC LIMIT ?)", (_INCIDENTS_KEEP_ROWS,))
    c.commit()


def init_db():
    """Создаёт БД/схему и чистит старьё. Вызывается один раз при старте app.py."""
    with _lock:
        c = _connect()
        _prune(c)


# ── Инциденты ─────────────────────────────────────────────────
def load_incidents():
    try:
        with _lock:
            rows = _connect().execute(
                "SELECT id, server, key, severity, msg, opened, closed, status "
                "FROM incidents ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[storage] load_incidents error: {e}")
        return []


def insert_incident(server, key, severity, msg, opened, status="open", closed=None):
    """Возвращает id новой записи (или None при ошибке)."""
    try:
        with _lock:
            c = _connect()
            cur = c.execute(
                "INSERT INTO incidents(server, key, severity, msg, opened, closed, status) "
                "VALUES(?,?,?,?,?,?,?)", (server, key, severity, msg, opened, closed, status))
            c.commit()
            return cur.lastrowid
    except Exception as e:
        print(f"[storage] insert_incident error: {e}")
        return None


def update_incident(inc_id, status, closed):
    try:
        with _lock:
            c = _connect()
            c.execute("UPDATE incidents SET status=?, closed=? WHERE id=?",
                      (status, closed, inc_id))
            c.commit()
    except Exception as e:
        print(f"[storage] update_incident error: {e}")


def delete_closed_incidents():
    try:
        with _lock:
            c = _connect()
            c.execute("DELETE FROM incidents WHERE status='closed'")
            c.commit()
    except Exception as e:
        print(f"[storage] delete_closed_incidents error: {e}")


# ── Метрики (sparkline) ───────────────────────────────────────
def load_metrics_history(limit=60):
    """Возвращает {server: {"cpu":[...], "ram":[...], "disk":[...]}} — последние `limit` точек."""
    out = {}
    try:
        with _lock:
            c = _connect()
            servers = [r[0] for r in c.execute("SELECT DISTINCT server FROM metrics").fetchall()]
            for srv in servers:
                rows = c.execute(
                    "SELECT cpu, ram, disk FROM metrics WHERE server=? ORDER BY ts DESC LIMIT ?",
                    (srv, limit)).fetchall()
                rows = list(reversed(rows))
                out[srv] = {
                    "cpu":  [r["cpu"]  for r in rows if r["cpu"]  is not None],
                    "ram":  [r["ram"]  for r in rows if r["ram"]  is not None],
                    "disk": [r["disk"] for r in rows if r["disk"] is not None],
                }
    except Exception as e:
        print(f"[storage] load_metrics_history error: {e}")
    return out


def insert_metric(server, ts, cpu, ram, disk):
    try:
        with _lock:
            c = _connect()
            c.execute("INSERT INTO metrics(server, ts, cpu, ram, disk) VALUES(?,?,?,?,?)",
                      (server, ts, cpu, ram, disk))
            c.commit()
    except Exception as e:
        print(f"[storage] insert_metric error: {e}")


# ── Аптайм по дням ────────────────────────────────────────────
def load_uptime_history():
    """Возвращает {server: {day: {"checks":n, "up":m}}}."""
    out = {}
    try:
        with _lock:
            rows = _connect().execute(
                "SELECT server, day, checks, up FROM uptime").fetchall()
        for r in rows:
            out.setdefault(r["server"], {})[r["day"]] = {"checks": r["checks"], "up": r["up"]}
    except Exception as e:
        print(f"[storage] load_uptime_history error: {e}")
    return out


def upsert_uptime(server, day, checks, up):
    try:
        with _lock:
            c = _connect()
            c.execute(
                "INSERT INTO uptime(server, day, checks, up) VALUES(?,?,?,?) "
                "ON CONFLICT(server, day) DO UPDATE SET checks=excluded.checks, up=excluded.up",
                (server, day, checks, up))
            c.commit()
    except Exception as e:
        print(f"[storage] upsert_uptime error: {e}")


# ── Журнал аудита ─────────────────────────────────────────────
def load_audit(limit=500):
    try:
        with _lock:
            rows = _connect().execute(
                "SELECT ts, server, cmd, rc FROM audit ORDER BY id DESC LIMIT ?",
                (limit,)).fetchall()
        return [dict(r) for r in reversed(rows)]
    except Exception as e:
        print(f"[storage] load_audit error: {e}")
        return []


def insert_audit(ts, server, cmd, rc):
    try:
        with _lock:
            c = _connect()
            c.execute("INSERT INTO audit(ts, server, cmd, rc) VALUES(?,?,?,?)",
                      (ts, server, cmd, rc))
            c.commit()
    except Exception as e:
        print(f"[storage] insert_audit error: {e}")


def clear_audit():
    try:
        with _lock:
            c = _connect()
            c.execute("DELETE FROM audit")
            c.commit()
    except Exception as e:
        print(f"[storage] clear_audit error: {e}")
