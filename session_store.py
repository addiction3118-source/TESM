# ─────────────────────────────────────────────────────────────
# session_store.py — «Запомнить меня» через защищённое хранилище ОС.
#
# Раньше мастер-пароль (расшифровывающий .keys.enc) сохранялся в файл
# .ba_session, «зашифрованный» XOR'ом по ключу из hostname+username —
# то есть фактически в восстановимом виде. Любой, кто прочитал файл,
# доставал пароль и все API-ключи.
#
# Теперь пароль кладётся в ОС-хранилище (keyring): на Windows это
# Credential Manager (шифрование DPAPI на пользователя), на macOS —
# Keychain, на Linux — Secret Service. Внутри хранится срок годности
# (TTL): по истечении сессия аннулируется и пароль спрашивается снова.
#
# Если keyring недоступен — «запомнить меня» просто отключается
# (пароль вводится каждый раз). В небезопасное хранилище НЕ падаем.
# ─────────────────────────────────────────────────────────────
import os
import json
import time

try:
    import keyring
    _KEYRING_OK = True
except Exception:
    _KEYRING_OK = False

import config

_DIR    = os.path.dirname(os.path.abspath(__file__))
_LEGACY = os.path.join(_DIR, ".ba_session")  # старый XOR-файл — удаляем
_USER   = "default"                          # одна запись на установку


def available():
    """keyring доступен → «запомнить меня» можно предлагать."""
    return _KEYRING_OK


def _purge_legacy():
    """Удаляет старый .ba_session: он хранил пароль обратимым XOR'ом
    и считается скомпрометированным."""
    try:
        if os.path.exists(_LEGACY):
            os.remove(_LEGACY)
    except Exception:
        pass


def _expired(exp):
    """Истёк ли срок годности сессии (pure — удобно тестировать)."""
    try:
        return time.time() >= float(exp)
    except Exception:
        return True


def save_session(pwd):
    _purge_legacy()
    if not _KEYRING_OK:
        return
    try:
        exp = time.time() + config.SESSION_TTL_HOURS * 3600
        keyring.set_password(config.SESSION_KEYRING_SERVICE, _USER,
                             json.dumps({"pwd": pwd, "exp": exp}))
    except Exception as e:
        print(f"[session] save error: {e}")


def load_session():
    """Возвращает сохранённый пароль, если сессия валидна и не истекла,
    иначе пустую строку."""
    _purge_legacy()
    if not _KEYRING_OK:
        return ""
    try:
        raw = keyring.get_password(config.SESSION_KEYRING_SERVICE, _USER)
        if not raw:
            return ""
        data = json.loads(raw)
        if _expired(data.get("exp", 0)):
            clear_session()
            return ""
        return data.get("pwd", "")
    except Exception as e:
        print(f"[session] load error: {e}")
        return ""


def clear_session():
    _purge_legacy()
    if not _KEYRING_OK:
        return
    try:
        keyring.delete_password(config.SESSION_KEYRING_SERVICE, _USER)
    except Exception:
        pass


def has_session():
    """Есть ли действующая запомненная сессия (без раскрытия пароля)."""
    if not _KEYRING_OK:
        return False
    try:
        raw = keyring.get_password(config.SESSION_KEYRING_SERVICE, _USER)
        if not raw:
            return False
        return not _expired(json.loads(raw).get("exp", 0))
    except Exception:
        return False
