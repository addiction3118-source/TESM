import os
import sys
import socket
import webbrowser
import threading
import time
import subprocess

<<<<<<< HEAD
REQUIRED_PACKAGES = [
    "groq",
    "google-generativeai",
    "openai",
    "python-dotenv",
    "psutil",  # для агента мониторинга
    "cryptography",  # AES-256 шифрование ключей
]

STREAMLIT_MIN_VERSION = (1, 33, 0)


def check_and_install():
    # Проверяем версию Streamlit
    try:
        import streamlit as _st
        ver = tuple(int(x) for x in _st.__version__.split(".")[:3])
        if ver < STREAMLIT_MIN_VERSION:
            min_ver = ".".join(str(x) for x in STREAMLIT_MIN_VERSION)
            print(f"⬆️  Streamlit {_st.__version__} → обновляем до {min_ver}+...")
            subprocess.run([sys.executable, "-m", "pip", "install", f"streamlit>={min_ver}"], check=True)
            print("✅ Streamlit обновлён.\n")
        else:
            print(f"✓ Streamlit {_st.__version__}")
    except ImportError:
        print("📦 Устанавливаем Streamlit...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit>=1.33.0"], check=True)
        print("✅ Streamlit установлен.\n")

    # Проверяем остальные пакеты
    missing = []
    for pkg in REQUIRED_PACKAGES:
        import_name = pkg.replace("-", "_").split(".")[0]
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"📦 Устанавливаем: {', '.join(missing)}...")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=True)
        print("✅ Установка завершена.\n")


def is_port_in_use(port):
=======

def is_port_in_use(port=8501):
>>>>>>> fd1828cefb60b37a5ae36e7e78a13604633b9489
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


<<<<<<< HEAD
def start_agent():
    """Запускает agent.py в фоне если он ещё не запущен."""
    if is_port_in_use(9999):
        print("✓ Агент уже запущен на порту 9999")
        return None

    current_dir = os.path.dirname(os.path.abspath(__file__))
    agent_path = os.path.join(current_dir, "agent.py")

    if not os.path.exists(agent_path):
        print("⚠️  agent.py не найден — CPU/RAM мониторинг недоступен")
        return None

    # Запускаем агент как отдельный процесс
    proc = subprocess.Popen(
        [sys.executable, agent_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Ждём пока агент поднимется
    deadline = time.time() + 5
    while time.time() < deadline:
        if is_port_in_use(9999):
            print("✅ Агент запущен на порту 9999 (CPU/RAM мониторинг активен)")
            return proc
        time.sleep(0.2)

    print("⚠️  Агент не ответил за 5 сек — запускается в фоне")
    return proc


def open_browser(port=8501, timeout=15):
=======
def open_browser(port=8501, timeout=15):
    """Открывает браузер когда Streamlit реально поднялся."""
>>>>>>> fd1828cefb60b37a5ae36e7e78a13604633b9489
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_port_in_use(port):
            time.sleep(0.3)
            webbrowser.open(f"http://localhost:{port}")
            return
        time.sleep(0.3)
<<<<<<< HEAD
    print("⚠️  Браузер не открыт — Streamlit не ответил.")


def load_env():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())


if __name__ == "__main__":
    print("🚀 Запуск TESM...\n")

    check_and_install()
    load_env()

    # Запускаем агент мониторинга
    agent_proc = start_agent()
=======
    print("⚠️  Браузер не открыт — Streamlit не ответил за отведённое время.")


if __name__ == "__main__":
    print("🚀 Запуск TESM...")
>>>>>>> fd1828cefb60b37a5ae36e7e78a13604633b9489

    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "app.py")

    if is_port_in_use(8501):
<<<<<<< HEAD
        print("⚠️  Порт 8501 уже занят.")

    threading.Thread(target=open_browser, daemon=True).start()

    print("\n🌐 Открываем браузер...\n")

    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.headless", "true",
        ])
    finally:
        # Останавливаем агент при закрытии TESM
        if agent_proc:
            agent_proc.terminate()
            print("🛑 Агент остановлен.")

    print("\n🛑 TESM завершён.")
=======
        print("⚠️  Порт 8501 уже занят — возможно, панель уже запущена.")

    threading.Thread(target=open_browser, daemon=True).start()

    subprocess.run([
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.headless", "true",
    ])
>>>>>>> fd1828cefb60b37a5ae36e7e78a13604633b9489
