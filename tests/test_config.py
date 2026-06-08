# Тесты структуры единого конфига (config.py).
# Проверяем, что ключевые константы объявлены и имеют корректную форму.
import config


def test_thresholds_shape():
    th = config.DEFAULT_THRESHOLDS
    assert set(th) == {"cpu", "ram", "disk"}
    assert all(isinstance(v, int) and 0 < v <= 100 for v in th.values())


def test_ssl_windows_ordered():
    # critical должен наступать раньше warning
    assert config.SSL_CRIT_DAYS < config.SSL_WARN_DAYS


def test_ports_and_timeouts_are_int():
    assert isinstance(config.AGENT_DEFAULT_PORT, int)
    for t in (config.HTTP_CHECK_TIMEOUT, config.AGENT_FETCH_TIMEOUT,
              config.EXEC_TIMEOUT, config.SSL_CONNECT_TIMEOUT):
        assert isinstance(t, int) and t > 0


def test_routing_complete():
    assert set(config.ROUTING) == {"code", "reasoning", "long", "general"}
    for provider, model, label in config.ROUTING.values():
        assert provider in ("groq", "gemini", "openai")
        assert model and label
