# ─────────────────────────────────────────────────────────────
# platform_cmds.py — команды управления службами и чтения логов,
# зависящие от ОС наблюдаемого сервера.
#
# Раньше вкладка «Службы/Логи» работала только под Linux (systemctl,
# /var/log, journalctl). Теперь команды строятся под нужную ОС: Linux
# (systemctl/tail) или Windows (PowerShell: Get-Service/Get-EventLog).
#
# Чистый модуль без побочных эффектов — удобно тестировать.
# ─────────────────────────────────────────────────────────────


def os_kind(os_name):
    """Нормализует platform.system()/os.name в 'windows' | 'linux' | 'unknown'."""
    if not os_name:
        return "unknown"
    o = str(os_name).lower()
    if o == "nt" or o.startswith("win"):   # не используем "win" in o — ловит "darwin"
        return "windows"
    if o == "posix" or "linux" in o:
        return "linux"
    return "unknown"


def list_services_cmd(kind):
    """Команда: список запущенных служб в формате строк «имя статус»."""
    if kind == "windows":
        return ("powershell -NoProfile -Command \"Get-Service | "
                "Where-Object {$_.Status -eq 'Running'} | Select-Object -First 30 | "
                "ForEach-Object { $_.Name + ' running' }\"")
    return ("systemctl list-units --type=service --state=running --no-pager "
            "--no-legend | awk '{print $1,$4}' | head -30")


def service_action_cmd(kind, action, svc):
    """Команда start/stop/restart/reload для службы."""
    if kind == "windows":
        verb = {"start": "Start-Service", "stop": "Stop-Service",
                "restart": "Restart-Service", "reload": "Restart-Service"}.get(action, "Get-Service")
        return (f"powershell -NoProfile -Command \"{verb} -Name '{svc}'; "
                f"(Get-Service -Name '{svc}').Status\"")
    return f"sudo systemctl {action} {svc}.service 2>&1; systemctl is-active {svc}.service"


def service_status_cmd(kind, svc):
    """Команда: подробный статус службы."""
    if kind == "windows":
        return (f"powershell -NoProfile -Command \"Get-Service -Name '{svc}' | "
                f"Format-List Name,Status,DisplayName\"")
    return f"systemctl status {svc}.service --no-pager -l 2>&1"


def default_log_source(kind):
    """Источник логов по умолчанию для ОС."""
    return "System" if kind == "windows" else "/var/log/syslog"


def fetch_log_cmd(kind, source, lines):
    """Команда: получить последние `lines` записей лога `source`."""
    if kind == "windows":
        return (f"powershell -NoProfile -Command \"Get-EventLog -LogName '{source}' "
                f"-Newest {int(lines)} | Format-Table -AutoSize -Wrap "
                f"TimeGenerated,EntryType,Source,Message\"")
    return f"tail -n {int(lines)} {source} 2>&1"
