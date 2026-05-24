import os
import re
import json
import socket
from datetime import datetime


def is_valid_hostname(hostname: str) -> bool:
    if not hostname or not hostname.strip():
        print("❌ Адрес не может быть пустым!")
        return False
    if len(hostname) > 255:
        print("❌ Слишком длинное имя (максимум 255 символов)!")
        return False
    if not re.match(r"^[a-zA-Z0-9.\-]+$", hostname):
        print("❌ Недопустимые символы! Только буквы, цифры, точки и дефисы.")
        return False
    if not re.search(r"\.", hostname):
        print("❌ Неполный домен — добавьте точку (например: example.com).")
        return False
    return True


def print_list(servers: dict):
    if not servers:
        print("   (список пуст)")
        return
    for name, host in servers.items():
        print(f"   {name:15} → {host}")


def configure_servers() -> dict:
    servers = {"ЛАТ": "luat.ru"}

    print("=" * 50)
    print("   TESM — настройка серверов")
    print("=" * 50)
    print("\nСтартовый сервер: ЛАТ → luat.ru\n")

    while True:
        print("[a] Добавить  [d] Удалить  [l] Список  [s] Сохранить и выйти")
        choice = input("Выбор: ").strip().lower()

        if choice == "a":
            name = input("  Имя среды: ").strip()
            if not name:
                print("  ❌ Имя не может быть пустым!\n"); continue
            if name in servers:
                print(f"  ❌ '{name}' уже существует!\n"); continue
            host = input(f"  Домен / IP для '{name}': ").strip()
            if not is_valid_hostname(host):
                print(); continue
            if host in servers.values():
                existing = next(k for k, v in servers.items() if v == host)
                print(f"  ⚠️  Хост уже добавлен под именем '{existing}'!\n"); continue
            servers[name] = host
            print(f"  ✅ Добавлен: {name} → {host}\n")

        elif choice == "d":
            if len(servers) == 1:
                print("  ⚠️  Нельзя удалить последний сервер!\n"); continue
            print("  Текущие серверы:")
            print_list(servers)
            name = input("  Имя для удаления: ").strip()
            if name in servers:
                del servers[name]
                print(f"  🗑️  Удалено: {name}\n")
            else:
                print(f"  ❌ '{name}' не найдено!\n")

        elif choice == "l":
            print("  Текущие серверы:")
            print_list(servers)
            print()

        elif choice == "s":
            break
        else:
            print("  Неизвестная команда.\n")

    return servers


if __name__ == "__main__":
    servers = configure_servers()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    temp_json = os.path.join(current_dir, "temp_servers.json")
    with open(temp_json, "w", encoding="utf-8") as f:
        json.dump(servers, f, ensure_ascii=False, indent=4)

    print(f"\n💾 Сохранено {len(servers)} сервер(ов) → temp_servers.json")
    print("   Теперь запусти run.py чтобы открыть панель.")
    print("=" * 50)