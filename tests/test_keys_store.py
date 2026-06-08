# Тесты шифрованного хранилища ключей (keys_store.py).
# Проверяем round-trip шифр/дешифр, неверный пароль, повреждённый файл.
# _KEYS_FILE подменяется на временный путь, чтобы не трогать реальный .keys.enc.
import pytest
import keys_store


@pytest.fixture
def tmp_keys(tmp_path, monkeypatch):
    p = tmp_path / "keys.enc"
    monkeypatch.setattr(keys_store, "_KEYS_FILE", str(p))
    return p


def test_roundtrip(tmp_keys):
    data = {"groq": "abc123", "openai": "xyz", "gemini": ""}
    assert keys_store.save_keys(data, "пароль123") is True
    assert keys_store.load_keys("пароль123") == data


def test_wrong_password_returns_none(tmp_keys):
    keys_store.save_keys({"groq": "secret"}, "правильный")
    assert keys_store.load_keys("неправильный") is None


def test_load_when_no_file(tmp_keys):
    assert keys_store.load_keys("любой") is None


def test_tampered_file_returns_none(tmp_keys):
    keys_store.save_keys({"groq": "secret"}, "pw")
    with open(tmp_keys, "w", encoding="ascii") as f:
        f.write("not-a-valid-base64-blob!!!")
    assert keys_store.load_keys("pw") is None


def test_exists_and_delete(tmp_keys):
    assert keys_store.keys_file_exists() is False
    keys_store.save_keys({"a": "b"}, "pw")
    assert keys_store.keys_file_exists() is True
    assert keys_store.delete_keys() is True
    assert keys_store.keys_file_exists() is False


def test_different_passwords_different_ciphertext(tmp_keys, tmp_path, monkeypatch):
    # Соль случайна → один и тот же контент шифруется по-разному.
    keys_store.save_keys({"k": "v"}, "pw")
    blob1 = tmp_keys.read_text()
    keys_store.save_keys({"k": "v"}, "pw")
    blob2 = tmp_keys.read_text()
    assert blob1 != blob2
