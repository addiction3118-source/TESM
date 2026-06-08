# Тесты построения команд служб/логов под разные ОС (platform_cmds.py).
import platform_cmds as pc


def test_os_kind():
    assert pc.os_kind("Windows") == "windows"
    assert pc.os_kind("nt") == "windows"
    assert pc.os_kind("Linux") == "linux"
    assert pc.os_kind("posix") == "linux"
    assert pc.os_kind("Darwin") == "unknown"
    assert pc.os_kind(None) == "unknown"
    assert pc.os_kind("") == "unknown"


def test_list_services_cmd():
    assert "systemctl" in pc.list_services_cmd("linux")
    assert "Get-Service" in pc.list_services_cmd("windows")


def test_service_action_cmd_linux():
    assert "systemctl restart nginx.service" in pc.service_action_cmd("linux", "restart", "nginx")


def test_service_action_cmd_windows():
    assert "Start-Service" in pc.service_action_cmd("windows", "start", "Spooler")
    assert "Stop-Service" in pc.service_action_cmd("windows", "stop", "Spooler")
    # reload на Windows сводится к restart
    assert "Restart-Service" in pc.service_action_cmd("windows", "reload", "Spooler")


def test_service_status_cmd():
    assert "systemctl status" in pc.service_status_cmd("linux", "nginx")
    assert "Get-Service" in pc.service_status_cmd("windows", "Spooler")


def test_default_log_source():
    assert pc.default_log_source("linux") == "/var/log/syslog"
    assert pc.default_log_source("windows") == "System"


def test_fetch_log_cmd():
    assert "tail -n 50" in pc.fetch_log_cmd("linux", "/var/log/syslog", 50)
    assert "Get-EventLog" in pc.fetch_log_cmd("windows", "System", 50)
    # количество строк приводится к int (защита от подстановки нечисла)
    assert "tail -n 20" in pc.fetch_log_cmd("linux", "/var/log/x", "20")
