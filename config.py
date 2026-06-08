# ─────────────────────────────────────────────────────────────
# config.py — единая точка настройки BlackArachnia.
#
# Раньше пороги, модели LLM, порты, таймауты и антиспам были «зашиты»
# в разных местах app.py / core.py / tg_bot.py. Теперь все значения здесь.
#
# Любую константу можно переопределить, положив рядом config.json, напр.:
#   { "DEFAULT_THRESHOLDS": {"cpu": 80, "ram": 85, "disk": 95},
#     "TG_COOLDOWN_MIN": 30 }
# Файл config.json не обязателен; без него используются значения ниже.
# ─────────────────────────────────────────────────────────────
import os
import json

_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Пороги инцидентов (%) ─────────────────────────────────────
DEFAULT_THRESHOLDS = {"cpu": 85, "ram": 90, "disk": 90}

# ── SSL: за сколько дней до истечения поднимать инцидент ───────
SSL_CRIT_DAYS = 14   # critical
SSL_WARN_DAYS = 30   # warning

# ── Антиспам Telegram-алертов (минуты между одинаковыми) ───────
TG_COOLDOWN_MIN = 15

# ── Агент мониторинга ─────────────────────────────────────────
AGENT_DEFAULT_PORT = 9999

# ── Сетевые таймауты (секунды) ────────────────────────────────
HTTP_CHECK_TIMEOUT  = 4    # проверка доступности сайта
SSL_CONNECT_TIMEOUT = 2    # подключение для чтения SSL-сертификата
AGENT_FETCH_TIMEOUT = 2    # опрос агента (/metrics, /processes)
EXEC_TIMEOUT        = 35   # выполнение удалённой команды (/exec)

# ── LLM-роутер: task → (провайдер, модель, подпись) ───────────
ROUTING = {
    "code":      ("groq",   "llama-3.3-70b-versatile", "Groq/Llama70B"),
    "reasoning": ("groq",   "llama-3.3-70b-versatile", "Groq/Llama70B"),
    "long":      ("gemini", "gemini-2.0-flash",        "Gemini Flash"),
    "general":   ("groq",   "llama-3.3-70b-versatile", "Groq/Llama70B"),
}

# Модели для ручного выбора провайдера (не auto)
GEMINI_MODEL, GEMINI_LABEL = "gemini-2.0-flash", "Gemini Flash"
OPENAI_MODEL, OPENAI_LABEL = "gpt-4o-mini",      "GPT-4o mini"

# ── Вход / сессия ─────────────────────────────────────────────
# Показывать кнопку «Войти без ключей» (для локального инструмента удобно).
ALLOW_SKIP_KEYS = True
# «Запомнить меня»: мастер-пароль хранится в ОС-хранилище (keyring),
# срок жизни — сколько часов до повторного запроса пароля.
SESSION_TTL_HOURS = 168            # 7 дней
SESSION_KEYRING_SERVICE = "BlackArachnia"


# ── Переопределение из config.json (если есть) ────────────────
def _apply_overrides():
    path = os.path.join(_DIR, "config.json")
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            user = json.load(f)
    except Exception as e:
        print(f"[config] не удалось прочитать config.json: {e}")
        return
    g = globals()
    for k, v in user.items():
        # Переопределяем только объявленные UPPER_CASE-константы.
        if k.isupper() and k in g:
            g[k] = v


_apply_overrides()
