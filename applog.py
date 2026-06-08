# ─────────────────────────────────────────────────────────────
# applog.py — файловое логирование BlackArachnia
#
# Раньше check_server/fetch_agent/exec_remote глушили все ошибки
# (except Exception: return {}), и «сервер офлайн», «неверный токен»
# и «сеть упала» выглядели одинаково. Теперь причины различаются и
# пишутся в файл blackarachnia.log (ротация, чтобы не рос бесконечно).
#
# Только стандартная библиотека (logging) — без новых зависимостей.
# ─────────────────────────────────────────────────────────────
import os
import logging
from logging.handlers import RotatingFileHandler

_DIR      = os.path.dirname(os.path.abspath(__file__))
_LOG_PATH = os.path.join(_DIR, "blackarachnia.log")

_logger = None


def get_logger():
    """Единый логгер процесса. Пишет в файл с уровня INFO (DEBUG не пишется,
    чтобы периодический опрос агента не спамил)."""
    global _logger
    if _logger is not None:
        return _logger
    lg = logging.getLogger("blackarachnia")
    lg.setLevel(logging.DEBUG)
    if not lg.handlers:
        try:
            fh = RotatingFileHandler(_LOG_PATH, maxBytes=1_000_000,
                                     backupCount=3, encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S"))
            lg.addHandler(fh)
        except Exception as e:
            # Логирование никогда не должно ронять приложение.
            print(f"[applog] не удалось открыть файл лога: {e}")
        lg.propagate = False
    _logger = lg
    return _logger
