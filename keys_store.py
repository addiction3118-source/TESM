# ─────────────────────────────────────────────────────────────
# keys_store.py — AES-256 шифрование API ключей
# Использует cryptography (PBKDF2 + AES-GCM)
# ─────────────────────────────────────────────────────────────
import os
import json
import base64

_DIR       = os.path.dirname(os.path.abspath(__file__))
_KEYS_FILE = os.path.join(_DIR, ".keys.enc")

# PBKDF2: 200_000 итераций — брутфорс занял бы годы
PBKDF2_ITERATIONS = 200_000
SALT_SIZE  = 16   # байт
NONCE_SIZE = 12   # байт (AES-GCM стандарт)
TAG_SIZE   = 16   # байт (AES-GCM тег аутентификации)


def _derive_key(password: str, salt: bytes) -> bytes:
    """PBKDF2-HMAC-SHA256 — медленный KDF, защита от брутфорса."""
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def save_keys(keys: dict, password: str) -> bool:
    """
    Шифрует ключи AES-256-GCM и сохраняет в файл.
    Формат: base64(salt + nonce + ciphertext + tag)
    """
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        salt  = os.urandom(SALT_SIZE)
        nonce = os.urandom(NONCE_SIZE)
        key   = _derive_key(password, salt)

        plaintext  = json.dumps(keys, ensure_ascii=False).encode("utf-8")
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
        # ciphertext уже содержит GCM-тег в конце (последние 16 байт)

        blob = base64.b64encode(salt + nonce + ciphertext).decode("ascii")
        with open(_KEYS_FILE, "w", encoding="ascii") as f:
            f.write(blob)
        return True
    except Exception as e:
        print(f"[keys_store] save error: {e}")
        return False


def load_keys(password: str) -> dict | None:
    """
    Расшифровывает ключи. Возвращает None если:
    - файла нет
    - пароль неверный (GCM-тег не совпадёт → InvalidTag)
    - файл повреждён
    """
    if not os.path.exists(_KEYS_FILE):
        return None
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.exceptions import InvalidTag

        with open(_KEYS_FILE, "r", encoding="ascii") as f:
            blob = f.read().strip()

        raw   = base64.b64decode(blob)
        salt  = raw[:SALT_SIZE]
        nonce = raw[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
        ciphertext = raw[SALT_SIZE + NONCE_SIZE:]

        key = _derive_key(password, salt)
        try:
            plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
        except InvalidTag:
            return None  # неверный пароль

        data = json.loads(plaintext.decode("utf-8"))
        return data if isinstance(data, dict) else None
    except Exception as e:
        print(f"[keys_store] load error: {e}")
        return None


def keys_file_exists() -> bool:
    return os.path.exists(_KEYS_FILE)


def delete_keys() -> bool:
    try:
        if os.path.exists(_KEYS_FILE):
            # Перезаписываем нулями перед удалением
            size = os.path.getsize(_KEYS_FILE)
            with open(_KEYS_FILE, "wb") as f:
                f.write(b"\x00" * size)
            os.remove(_KEYS_FILE)
        return True
    except Exception:
        return False