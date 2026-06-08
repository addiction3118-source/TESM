# Тесты «Запомнить меня» (session_store.py).
# keyring подменяется фейковым in-memory бэкендом, реальное ОС-хранилище
# и файл .ba_session не трогаются.
import json
import time

import pytest

import session_store


class FakeKeyring:
    def __init__(self):
        self.store = {}

    def set_password(self, service, user, value):
        self.store[(service, user)] = value

    def get_password(self, service, user):
        return self.store.get((service, user))

    def delete_password(self, service, user):
        if (service, user) in self.store:
            del self.store[(service, user)]
        else:
            raise Exception("not found")


@pytest.fixture
def fake_kr(monkeypatch, tmp_path):
    fk = FakeKeyring()
    monkeypatch.setattr(session_store, "keyring", fk, raising=False)
    monkeypatch.setattr(session_store, "_KEYRING_OK", True)
    # .ba_session не трогаем — направляем во временную папку
    monkeypatch.setattr(session_store, "_LEGACY", str(tmp_path / ".ba_session"))
    return fk


def test_expired_pure():
    assert session_store._expired(time.time() - 1) is True
    assert session_store._expired(time.time() + 1000) is False
    assert session_store._expired("мусор") is True  # некорректное значение → истёк


def test_roundtrip(fake_kr):
    session_store.save_session("hunter2")
    assert session_store.load_session() == "hunter2"
    assert session_store.has_session() is True


def test_clear(fake_kr):
    session_store.save_session("secret")
    session_store.clear_session()
    assert session_store.load_session() == ""
    assert session_store.has_session() is False


def test_ttl_expiry(fake_kr, monkeypatch):
    monkeypatch.setattr(session_store.config, "SESSION_TTL_HOURS", -1)  # сразу истёкший
    session_store.save_session("secret")
    assert session_store.load_session() == ""
    assert session_store.has_session() is False


def test_no_keyring_disables_remember(monkeypatch, tmp_path):
    monkeypatch.setattr(session_store, "_KEYRING_OK", False)
    monkeypatch.setattr(session_store, "_LEGACY", str(tmp_path / ".ba_session"))
    session_store.save_session("secret")          # no-op
    assert session_store.load_session() == ""
    assert session_store.available() is False


def test_legacy_file_purged(monkeypatch, tmp_path):
    legacy = tmp_path / ".ba_session"
    legacy.write_text("old-xor-blob")
    monkeypatch.setattr(session_store, "_LEGACY", str(legacy))
    monkeypatch.setattr(session_store, "_KEYRING_OK", False)
    session_store.load_session()
    assert not legacy.exists()  # старый небезопасный файл удалён


def test_stored_value_has_no_plaintext_in_legacy(fake_kr):
    # Пароль уходит в keyring (фейковый), а не в файл проекта.
    session_store.save_session("p@ss")
    raw = fake_kr.get_password(session_store.config.SESSION_KEYRING_SERVICE, "default")
    assert json.loads(raw)["pwd"] == "p@ss"
