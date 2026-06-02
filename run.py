import os
import sys
import socket
import webbrowser
import threading
import time
import subprocess
import importlib.util

# ── Минимальные версии ─────────────────────────────────────────
STREAMLIT_MIN = (1, 33, 0)

# ── Пакеты: (import_name, pip_name) ───────────────────────────
PACKAGES = [
    ("streamlit",       "streamlit>=1.33.0"),
    ("groq",            "groq"),
    ("google.generativeai", "google-generativeai"),
    ("openai",          "openai"),
    ("dotenv",          "python-dotenv"),
    ("psutil",          "psutil"),
    ("cryptography",    "cryptography"),
]


def pkg_installed(import_name: str) -> bool:
    """Проверяет наличие пакета через importlib — без импорта."""
    return importlib.util.find_spec(import_name) is not None


def check_and_install():
    """
    Быстрая проверка: импортирует только то чего нет.
    Если всё установлено — запуск занимает < 1 сек.
    """
    missing_pip = []

    # Streamlit — проверяем версию отдельно
    if pkg_installed("streamlit"):
        try:
            import streamlit as _st
            ver = tuple(int(x) for x in _st.__version__.split(".")[:3])
            if ver < STREAMLIT_MIN:
                min_str = ".".join(str(x) for x in STREAMLIT_MIN)
                print(f"⬆️  Streamlit {_st.__version__} устарел → обновляем до {min_str}+")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", f"streamlit>={min_str}",
                     "--quiet", "--disable-pip-version-check"],
                    check=True
                )
                print("✅ Streamlit обновлён")
            else:
                print(f"✓ Streamlit {_st.__version__}")
        except Exception as e:
            print(f"⚠️  Ошибка проверки Streamlit: {e}")
    else:
        missing_pip.append("streamlit>=1.33.0")

    # Остальные пакеты — только проверка через find_spec (мгновенно)
    for import_name, pip_name in PACKAGES[1:]:
        top_level = import_name.split(".")[0]
        if not pkg_installed(top_level):
            missing_pip.append(pip_name)
        else:
            print(f"✓ {pip_name.split('>=')[0].split('[')[0]}")

    # Устанавливаем только то чего нет
    if missing_pip:
        print(f"\n📦 Устанавливаем: {', '.join(missing_pip)}")
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + missing_pip +
            ["--quiet", "--disable-pip-version-check"],
            check=True
        )
        print("✅ Установка завершена\n")
    else:
        print("✅ Все зависимости установлены\n")


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("localhost", port)) == 0


def start_agent():
    """Запускает agent.py в фоне если он ещё не запущен."""
    if is_port_in_use(9999):
        print("✓ Агент уже запущен на порту 9999")
        return None

    current_dir = os.path.dirname(os.path.abspath(__file__))
    agent_path  = os.path.join(current_dir, "agent.py")

    if not os.path.exists(agent_path):
        print("⚠️  agent.py не найден — CPU/RAM мониторинг недоступен")
        return None

    proc = subprocess.Popen(
        [sys.executable, agent_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.time() + 5
    while time.time() < deadline:
        if is_port_in_use(9999):
            print("✅ Агент запущен на порту 9999 (CPU/RAM мониторинг активен)")
            return proc
        time.sleep(0.15)

    print("⚠️  Агент запускается в фоне")
    return proc


def open_browser(port: int = 8501, timeout: int = 20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_port_in_use(port):
            time.sleep(0.4)
            webbrowser.open(f"http://localhost:{port}")
            return
        time.sleep(0.3)
    print("⚠️  Браузер не открыт — Streamlit не ответил за 20 сек")


def start_tg_bot():
    """Запускает Telegram-бота в фоне, если задан TG_BOT_TOKEN в .env."""
    if not os.environ.get("TG_BOT_TOKEN", "").strip():
        print("ℹ️  Telegram-бот не запущен (нет TG_BOT_TOKEN в .env)")
        return None
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bot_path    = os.path.join(current_dir, "tg_bot.py")
    if not os.path.exists(bot_path):
        return None
    proc = subprocess.Popen(
        [sys.executable, bot_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("🤖 Telegram-бот запущен (управление через мессенджер)")
    return proc


def load_env():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path    = os.path.join(current_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())


if __name__ == "__main__":
    print("🕷️  BlackArachnia — запуск...\n")

    t0 = time.time()
    check_and_install()
    load_env()

    agent_proc = start_agent()
    bot_proc   = start_tg_bot()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path    = os.path.join(current_dir, "app.py")

    if is_port_in_use(8501):
        print("⚠️  Порт 8501 уже занят — возможно приложение уже запущено")

    threading.Thread(target=open_browser, daemon=True).start()

    print(f"🌐 Открываем браузер...  (подготовка заняла {time.time()-t0:.1f} сек)\n")

    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.headless", "true",
            "--server.port", "8501",
        ])
    finally:
        if agent_proc:
            agent_proc.terminate()
            print("🛑 Агент остановлен")
        if bot_proc:
            bot_proc.terminate()
            print("🛑 Telegram-бот остановлен")

    print("🛑 BlackArachnia завершён")