# ─────────────────────────────────────────────────────────────
# i18n.py — переводы интерфейса (RU/EN), вынесено из app.py.
# ─────────────────────────────────────────────────────────────
import streamlit as st


TR = {
"ru": {
 "monitoring":"МОНИТОРИНГ","auto_refresh":"Авто-обновление (15с)","environment":"ОКРУЖЕНИЕ",
 "api_keys":"API КЛЮЧИ","agent_token":"ТОКЕН АГЕНТА","export":"ЭКСПОРТ","sysprompt":"СИСТЕМНЫЙ ПРОМПТ",
 "save_keys":"Сохранить ключи","encrypt_save":"Зашифровать и сохранить","password":"Пароль",
 "report_md":"📄 Отчёт .md","language":"ЯЗЫК","session":"СЕССИЯ","forget":"🚪 Забыть меня",
 "tg_section":"TELEGRAM","tg_enable":"Включить алерты","tg_test":"🔔 Тест",
 "tg_hint":"Токен у @BotFather, chat_id у @userinfobot. Напиши боту /start!",
 "tg_cooldown":"Кулдаун (мин)",
 "tab_dashboard":"Дашборд","tab_overview":"Сервер","tab_services":"Службы","tab_terminal":"Терминал",
 "tab_ai":"ИИ Чат","tab_incidents":"Инциденты","tab_logs":"Логи","tab_add":"Добавить",
 "status":"СТАТУС","uptime":"АПТАЙМ","http":"HTTP","ssl":"SSL","uptime90":"АПТАЙМ 90Д",
 "resources":"РЕСУРСЫ","network":"СЕТЬ","top_proc":"ТОП ПРОЦЕССОВ","all_servers":"ВСЕ СЕРВЕРЫ",
 "no_agent":"CPU/RAM — запусти agent.py на сервере","legend":"■ ≥99% · ■ ≥90% · ■ <90% · ■ нет данных",
 "online":"Онлайн","offline":"Офлайн","pending":"Ожидание",
 "console":"Консоль","snippets":"Сниппеты","audit":"Аудит","clear":"🗑 Очистить","run":"▶ Запуск",
 "cmd_ph":"$ команда...","history":"История","dl_txt":"💾 .txt","add_snippet":"➕ Добавить сниппет",
 "save":"Сохранить","name":"Название","command":"Команда",
 "analyze":"🔍 Анализ","clear_chat":"🗑 Очистить","chat_ph":"Спроси о серверах...",
 "chat_empty":"Начни диалог — ИИ знает состояние серверов и помнит контекст","send_term":"▶ В терминал",
 "thinking":"Думаю...","q_cmd":"💡 Команда","q_report":"📊 Отчёт","q_sec":"🛡 Безопасность",
 "inc_open":"Открытых","inc_crit":"Критичных","inc_warn":"Предупреждений","inc_total":"Всего",
 "thresholds":"⚙️ Пороги","no_inc":"Нет инцидентов","resolve":"✓ Закрыть","clear_closed":"🗑 Закрытые",
 "svc_title":"SYSTEMD СЛУЖБЫ","svc_refresh":"🔄 Обновить","log_stream":"СТРИМИНГ ЛОГОВ","log_get":"📡 Получить",
 "add_title":"ДОБАВИТЬ СЕРВЕР","test_agent":"🔍 Тест агента","add_server":"＋ Добавить",
 "cur_servers":"ТЕКУЩИЕ СЕРВЕРЫ","srv_name":"Имя","srv_host":"Хост / IP","agent_port":"Порт агента",
 "filter_ph":"Фильтр...","total":"Всего","shown":"Показано",
},
"en": {
 "monitoring":"MONITORING","auto_refresh":"Auto-refresh (15s)","environment":"ENVIRONMENT",
 "api_keys":"API KEYS","agent_token":"AGENT TOKEN","export":"EXPORT","sysprompt":"SYSTEM PROMPT",
 "save_keys":"Save keys","encrypt_save":"Encrypt & save","password":"Password",
 "report_md":"📄 Report .md","language":"LANGUAGE","session":"SESSION","forget":"🚪 Forget me",
 "tg_section":"TELEGRAM","tg_enable":"Enable alerts","tg_test":"🔔 Test",
 "tg_hint":"Token from @BotFather, chat_id from @userinfobot. Send /start to bot!",
 "tg_cooldown":"Cooldown (min)",
 "tab_dashboard":"Dashboard","tab_overview":"Server","tab_services":"Services","tab_terminal":"Terminal",
 "tab_ai":"AI Chat","tab_incidents":"Incidents","tab_logs":"Logs","tab_add":"Add",
 "status":"STATUS","uptime":"UPTIME","http":"HTTP","ssl":"SSL","uptime90":"UPTIME 90D",
 "resources":"RESOURCES","network":"NETWORK","top_proc":"TOP PROCESSES","all_servers":"ALL SERVERS",
 "no_agent":"CPU/RAM — run agent.py on server","legend":"■ ≥99% · ■ ≥90% · ■ <90% · ■ no data",
 "online":"Online","offline":"Offline","pending":"Pending",
 "console":"Console","snippets":"Snippets","audit":"Audit","clear":"🗑 Clear","run":"▶ Run",
 "cmd_ph":"$ command...","history":"History","dl_txt":"💾 .txt","add_snippet":"➕ Add snippet",
 "save":"Save","name":"Name","command":"Command",
 "analyze":"🔍 Analyze","clear_chat":"🗑 Clear","chat_ph":"Ask about servers...",
 "chat_empty":"Start chatting — AI knows server state and remembers context","send_term":"▶ To terminal",
 "thinking":"Thinking...","q_cmd":"💡 Command","q_report":"📊 Report","q_sec":"🛡 Security",
 "inc_open":"Open","inc_crit":"Critical","inc_warn":"Warning","inc_total":"Total",
 "thresholds":"⚙️ Thresholds","no_inc":"No incidents","resolve":"✓ Resolve","clear_closed":"🗑 Closed",
 "svc_title":"SYSTEMD SERVICES","svc_refresh":"🔄 Refresh","log_stream":"LOG STREAMING","log_get":"📡 Fetch",
 "add_title":"ADD SERVER","test_agent":"🔍 Test agent","add_server":"＋ Add",
 "cur_servers":"CURRENT SERVERS","srv_name":"Name","srv_host":"Host / IP","agent_port":"Agent port",
 "filter_ph":"Filter...","total":"Total","shown":"Shown",
},
}

def T(k):
    return TR.get(st.session_state.get("lang","ru"), TR["ru"]).get(k, k)
