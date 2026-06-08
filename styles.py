# ─────────────────────────────────────────────────────────────
# styles.py — CSS-тема BlackArachnia (вынесено из app.py).
# inject() вызывается из app.py ПОСЛЕ st.set_page_config.
# ─────────────────────────────────────────────────────────────
import streamlit as st


def inject():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    *,*::before,*::after { box-sizing:border-box; }
    [data-testid="stStatusWidget"],[data-testid="stDecoration"],
    [data-testid="stToolbar"],header[data-testid="stHeader"],
    #MainMenu,footer { display:none!important; }
    .block-container { padding:0!important; max-width:100%!important; }
    [data-testid="stAppViewContainer"] { padding:0!important; }

    .stApp { background:#0a0612!important; color:#ede6f3!important;
             font-family:'Inter',system-ui,sans-serif!important; }

    /* Sidebar — статичный, не сворачивается */
    [data-testid="stSidebar"] {
        background:#120a1f!important; border-right:1px solid #2a1a3d!important;
        min-width:225px!important; max-width:225px!important; transform:none!important;
    }
    [data-testid="stSidebarCollapsedControl"] { display:none!important; }
    [data-testid="stSidebar"] * { color:#8b949e!important; font-size:12px!important; }
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stTextArea textarea,
    [data-testid="stSidebar"] .stNumberInput input {
        background:#0a0612!important; border:1px solid #3d2459!important;
        color:#e6edf3!important; font-size:12px!important; border-radius:6px!important; }
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background:#0a0612!important; border:1px solid #3d2459!important;
        color:#e6edf3!important; border-radius:6px!important; }
    [data-testid="stSidebar"] .stButton > button {
        background:#2a1a3d!important; border:1px solid #3d2459!important;
        color:#8b949e!important; border-radius:6px!important; width:100%!important; }
    [data-testid="stSidebar"] .stButton > button:hover {
        background:#3d2459!important; color:#e6edf3!important; }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background:#0a0612!important; border:1px solid #2a1a3d!important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background:#150d24!important; border-bottom:1px solid #2a1a3d!important;
        gap:0!important; padding:0 16px!important; }
    .stTabs [data-baseweb="tab"] {
        background:transparent!important; color:#8b949e!important;
        font-size:12px!important; font-weight:500!important; padding:10px 14px!important;
        border-radius:0!important; border-bottom:2px solid transparent!important;
        letter-spacing:0.02em!important; text-transform:uppercase!important; }
    .stTabs [aria-selected="true"] {
        color:#bf5fff!important; border-bottom:2px solid #bf5fff!important;
        background:transparent!important; }

    /* Метрики */
    [data-testid="stMetric"] {
        background:#150d24!important; border:1px solid #2a1a3d!important;
        border-radius:8px!important; padding:14px 16px!important; }
    [data-testid="stMetricLabel"] { color:#8b949e!important; font-size:10px!important;
        font-weight:500!important; letter-spacing:0.08em!important;
        text-transform:uppercase!important; }
    [data-testid="stMetricValue"] { color:#e6edf3!important; font-size:20px!important;
        font-weight:600!important; font-family:'JetBrains Mono',monospace!important; }
    [data-testid="stMetricDelta"] { font-size:11px!important; }

    /* Кнопки */
    .stButton > button { background:#2a1a3d!important; color:#8b949e!important;
        border:1px solid #3d2459!important; border-radius:6px!important;
        font-size:12px!important; font-weight:500!important; transition:all .15s!important; }
    .stButton > button:hover { background:#3d2459!important; color:#e6edf3!important;
        border-color:#bf5fff!important; box-shadow:0 0 8px rgba(191,95,255,.4)!important; }

    /* Inputs */
    .stTextInput input,.stTextArea textarea {
        background:#150d24!important; color:#e6edf3!important;
        border:1px solid #3d2459!important; border-radius:6px!important;
        font-size:13px!important; }
    .stTextInput input:focus,.stTextArea textarea:focus {
        border-color:#bf5fff!important; box-shadow:0 0 0 3px rgba(191,95,255,.25)!important; }
    .stSelectbox > div > div { background:#150d24!important; border:1px solid #3d2459!important;
        color:#e6edf3!important; border-radius:6px!important; font-size:13px!important; }
    .stNumberInput input { background:#150d24!important; color:#e6edf3!important;
        border:1px solid #3d2459!important; border-radius:6px!important; }

    /* Alerts */
    .stSuccess { background:#0d2a1a!important; border:1px solid #238636!important;
        border-radius:6px!important; color:#3fb950!important; }
    .stError { background:#2d0f0f!important; border:1px solid #da3633!important;
        border-radius:6px!important; color:#ff7b72!important; }
    .stInfo { background:#0c2233!important; border:1px solid #388bfd!important;
        border-radius:6px!important; color:#bf5fff!important; }
    .stWarning { background:#2a1f00!important; border:1px solid #d29922!important;
        border-radius:6px!important; color:#e3b341!important; }
    [data-testid="stAlert"] { font-size:12px!important; }

    /* Expander / DataFrame / Chat / Code */
    [data-testid="stExpander"] { background:#150d24!important;
        border:1px solid #2a1a3d!important; border-radius:8px!important; }
    [data-testid="stExpander"] summary { color:#8b949e!important; font-size:12px!important; }
    [data-testid="stDataFrame"] { border:1px solid #2a1a3d!important;
        border-radius:8px!important; overflow:hidden!important; background:#0a0612!important; }
    [data-testid="stDataFrame"] * { background:#0a0612!important; color:#c9d1d9!important; }
    [data-testid="stDataFrame"] th { background:#150d24!important; color:#8b949e!important;
        font-size:11px!important; text-transform:uppercase!important; }
    [data-testid="stDataFrame"] td { background:#0a0612!important; color:#c9d1d9!important;
        font-size:12px!important; font-family:'JetBrains Mono',monospace!important; }
    [data-testid="stChatInput"] { background:#150d24!important;
        border:1px solid #3d2459!important; border-radius:8px!important; }
    [data-testid="stChatInput"] textarea { background:#150d24!important; color:#e6edf3!important; }
    [data-testid="stChatMessage"] { background:#150d24!important;
        border:1px solid #2a1a3d!important; border-radius:8px!important; margin-bottom:6px!important; }
    [data-testid="stChatMessage"] p { color:#c9d1d9!important; font-size:13px!important; }
    .stCode,code,pre { background:#150d24!important; color:#e6edf3!important;
        border:1px solid #2a1a3d!important; border-radius:6px!important;
        font-size:12px!important; font-family:'JetBrains Mono',monospace!important; }
    .stCaption { color:#6e7681!important; font-size:11px!important; }
    .stToggle label { color:#8b949e!important; font-size:12px!important; }
    hr { border-color:#2a1a3d!important; }


    /* Анти-мигание при авто-обновлении фрагмента */
    [data-testid="stAppViewContainer"] * { animation-duration:0s!important; }
    .element-container { transition:none!important; }
    [data-stale="true"], [data-stale="false"] {
        opacity:1!important; transition:none!important; filter:none!important;
    }
    [data-testid="stVerticalBlock"] { transition:none!important; }
    /* Скрываем индикатор "running" вверху справа */
    [data-testid="stStatusWidget"] { display:none!important; }
    .stSpinner { display:none!important; }


    /* ════ НЕОНОВЫЕ ЭФФЕКТЫ ════ */
    /* Активная вкладка — свечение */
    .stTabs [aria-selected="true"] {
        text-shadow:0 0 8px rgba(191,95,255,.8)!important;
    }
    /* Метрики — фиолетовая рамка со свечением */
    [data-testid="stMetric"] {
        box-shadow:0 0 0 1px rgba(191,95,255,.15), 0 2px 12px rgba(191,95,255,.08)!important;
    }
    [data-testid="stMetricValue"] {
        color:#d9a6ff!important; text-shadow:0 0 10px rgba(191,95,255,.5)!important;
    }
    /* Кнопки при наведении — неоновый край */
    .stButton > button:hover {
        box-shadow:0 0 12px rgba(191,95,255,.5)!important;
        text-shadow:0 0 6px rgba(191,95,255,.6)!important;
    }
    /* Заголовок в шапке — свечение */
    .ba-glow { text-shadow:0 0 12px rgba(191,95,255,.7); }
    /* Чат-инпут focus */
    [data-testid="stChatInput"]:focus-within {
        box-shadow:0 0 14px rgba(191,95,255,.4)!important;
    }
    /* Скроллбары фиолетовые */
    ::-webkit-scrollbar { width:8px; height:8px; }
    ::-webkit-scrollbar-track { background:#0a0612; }
    ::-webkit-scrollbar-thumb { background:#3d2459; border-radius:4px; }
    ::-webkit-scrollbar-thumb:hover { background:#bf5fff; }
    /* Градиентная полоса сверху приложения */
    .stApp::before {
        content:""; position:fixed; top:0; left:0; right:0; height:2px; z-index:99999;
        background:linear-gradient(90deg,transparent,#bf5fff,#7b2fde,#bf5fff,transparent);
        box-shadow:0 0 10px rgba(191,95,255,.6);
    }


    /* ════ УСИЛЕННЫЙ НЕОН ════ */
    /* Sidebar — неоновая правая граница со свечением */
    [data-testid="stSidebar"] {
        border-right:1px solid rgba(191,95,255,.35)!important;
        box-shadow:4px 0 24px rgba(191,95,255,.12)!important;
    }
    /* Все текстовые поля — неоновая обводка */
    .stTextInput input, .stTextArea textarea, .stNumberInput input,
    .stSelectbox > div > div, [data-testid="stChatInput"] {
        border:1px solid rgba(191,95,255,.3)!important;
        box-shadow:inset 0 0 8px rgba(191,95,255,.06)!important;
        transition:all .2s ease!important;
    }
    .stTextInput input:hover, .stTextArea textarea:hover,
    .stNumberInput input:hover, .stSelectbox > div > div:hover {
        border-color:rgba(191,95,255,.6)!important;
        box-shadow:0 0 10px rgba(191,95,255,.25)!important;
    }
    /* Кнопки — мягкая неоновая обводка постоянно */
    .stButton > button {
        border:1px solid rgba(191,95,255,.25)!important;
        transition:all .2s ease!important;
    }
    /* Метрики — неоновая рамка + градиентный фон */
    [data-testid="stMetric"] {
        background:linear-gradient(135deg, #150d24 0%, #1a0f2e 100%)!important;
        border:1px solid rgba(191,95,255,.3)!important;
        box-shadow:0 0 0 1px rgba(191,95,255,.1), 0 4px 20px rgba(191,95,255,.1)!important;
        transition:all .25s ease!important;
    }
    [data-testid="stMetric"]:hover {
        border-color:rgba(191,95,255,.55)!important;
        box-shadow:0 0 20px rgba(191,95,255,.25)!important;
        transform:translateY(-2px);
    }
    /* Карточки ресурсов и серверов — неоновая обводка */
    .res-card, .dash-card {
        border:1px solid rgba(191,95,255,.25)!important;
        box-shadow:0 2px 16px rgba(191,95,255,.08)!important;
        transition:all .25s ease!important;
    }
    .res-card:hover, .dash-card:hover {
        border-color:rgba(191,95,255,.5)!important;
        box-shadow:0 0 18px rgba(191,95,255,.2)!important;
    }
    /* Экспандеры — неон */
    [data-testid="stExpander"] {
        border:1px solid rgba(191,95,255,.25)!important;
        box-shadow:0 0 12px rgba(191,95,255,.06)!important;
    }
    /* Тоггл (включатель) — фиолетовый когда активен */
    [data-testid="stSidebar"] [aria-checked="true"] {
        background:#bf5fff!important;
    }
    /* Chat-сообщения — лёгкая обводка */
    [data-testid="stChatMessage"] {
        border:1px solid rgba(191,95,255,.2)!important;
        box-shadow:0 2px 12px rgba(191,95,255,.06)!important;
    }
    /* Логотип в шапке + sidebar — пульсация свечения */
    @keyframes neon-pulse {
        0%,100% { text-shadow:0 0 8px rgba(191,95,255,.5); }
        50%     { text-shadow:0 0 16px rgba(191,95,255,.9), 0 0 24px rgba(191,95,255,.4); }
    }
    .ba-glow { animation:neon-pulse 3s ease-in-out infinite; }
    /* Заголовки секций sidebar — фиолетовый акцент слева */
    [data-testid="stSidebar"] .stButton > button:hover {
        background:rgba(191,95,255,.12)!important;
    }


    /* Фикс белых полей в sidebar (password reveal, кнопка глаза) */
    [data-testid="stSidebar"] input { background:#0a0612!important; color:#ede6f3!important; }
    [data-testid="stSidebar"] [data-testid="stTextInput"] > div,
    [data-testid="stSidebar"] [data-testid="stTextInput"] > div > div {
        background:#0a0612!important; border-radius:6px!important;
    }
    [data-testid="stSidebar"] button[title="Show password text"],
    [data-testid="stSidebar"] button[title="Hide password text"] {
        background:#0a0612!important; color:#bf5fff!important;
    }
    /* Кнопки RU/EN и активные — градиент при наведении */
    [data-testid="stSidebar"] .stButton > button:active {
        background:linear-gradient(135deg, rgba(191,95,255,.3), rgba(123,47,222,.3))!important;
    }

    /* Прогресс-бар */
    .nd-bar-wrap { height:4px; background:#2a1a3d; border-radius:2px; overflow:hidden; margin-top:3px; }
    .nd-bar-fill { height:100%; border-radius:2px; box-shadow:0 0 8px currentColor; filter:brightness(1.1); }


    /* Статус-dot */
    .dot { display:inline-block; width:7px; height:7px; border-radius:50%; margin-right:5px; }
    .dot-green  { background:#3fb950; box-shadow:0 0 6px #3fb950; }
    .dot-red    { background:#f85149; box-shadow:0 0 6px #f85149; }
    .dot-yellow { background:#e3b341; box-shadow:0 0 6px #e3b341; }

    /* Uptime 90 дней */
    .upt-grid { display:flex; gap:2px; flex-wrap:wrap; margin:6px 0; }
    .upt-cell { width:10px; height:20px; border-radius:2px; }

    /* Incident badge */
    .inc-badge { display:inline-block; padding:2px 8px; border-radius:12px;
        font-size:10px; font-weight:600; letter-spacing:0.05em; }
    .inc-critical { background:#2d0f0f; color:#ff7b72; border:1px solid #f85149; }
    .inc-warning  { background:#2a1f00; color:#e3b341; border:1px solid #d29922; }
    .inc-ok       { background:#0d2a1a; color:#3fb950; border:1px solid #238636; }

    /* Карточка ресурса */
    .res-card { background:#150d24; border:1px solid #2a1a3d; border-radius:8px; padding:12px 14px; }
    .res-label { font-size:10px; color:#6e7681; letter-spacing:0.08em; text-transform:uppercase; }
    .res-value { font-size:22px; font-weight:600; color:#e6edf3;
        font-family:'JetBrains Mono',monospace; margin:4px 0; }

    /* Дашборд-карточка сервера */
    .dash-card { background:#150d24; border:1px solid #2a1a3d; border-radius:10px;
        padding:14px 16px; margin-bottom:8px; }
    .dash-card.online  { border-left:3px solid #3fb950; }
    .dash-card.offline { border-left:3px solid #f85149; }
    .dash-card.pending { border-left:3px solid #e3b341; }

    /* Паутина */
    .spider-wrap { position:fixed; top:0; right:0; width:160px; height:160px;
        pointer-events:none; z-index:9999; overflow:hidden; }
    @keyframes spider-drop { 0%{top:8px} 100%{top:100px} }
    .spider { position:absolute; font-size:16px; right:16px; filter:drop-shadow(0 0 6px #bf5fff);
        animation:spider-drop 4s ease-in-out infinite alternate; }
    .spider-thread { position:absolute; top:0; right:26px; width:1px;
        background:linear-gradient(to bottom,#3d2459,transparent); height:110px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* ════════ НЕОН-GLASS PASS ════════ */
    /* Aurora — как фиксированный фон самого .stApp (не перекрывает контент,
       не ломает скролл сайдбара) */
    .stApp{
      background:
        radial-gradient(42vw 42vw at 10% 4%,  rgba(123,47,222,.30), transparent 60%),
        radial-gradient(48vw 48vw at 92% 96%, rgba(34,211,238,.15), transparent 62%),
        radial-gradient(34vw 34vw at 84% 6%,  rgba(191,95,255,.18), transparent 60%),
        #0a0612 !important;
      background-attachment:fixed !important;
    }
    /* Верхняя полоса — два акцента */
    .stApp::before{background:linear-gradient(90deg,transparent,#bf5fff,#22d3ee,#bf5fff,transparent)!important;}

    /* Стеклянные карточки (glassmorphism) */
    [data-testid="stMetric"], .res-card, .dash-card{
      background:linear-gradient(135deg, rgba(26,15,46,.62), rgba(16,9,28,.62))!important;
      backdrop-filter:blur(14px) saturate(150%);-webkit-backdrop-filter:blur(14px) saturate(150%);
      border:1px solid rgba(191,95,255,.30)!important;
      box-shadow:0 10px 32px rgba(0,0,0,.38), 0 0 0 1px rgba(191,95,255,.07),
                 inset 0 1px 0 rgba(255,255,255,.05)!important;
    }
    [data-testid="stMetric"]:hover, .res-card:hover, .dash-card:hover{
      border-color:rgba(34,211,238,.55)!important;
      box-shadow:0 14px 40px rgba(0,0,0,.45), 0 0 22px rgba(34,211,238,.18)!important;
    }
    [data-testid="stMetricValue"]{font-size:26px!important;
      background:linear-gradient(90deg,#d9a6ff,#22d3ee);-webkit-background-clip:text;background-clip:text;
      -webkit-text-fill-color:transparent;text-shadow:none!important;}

    /* Радиальные гейджи */
    .gauge-card{display:flex;flex-direction:column;align-items:center;gap:6px;padding:14px 8px!important;}
    .gauge{position:relative;display:flex;align-items:center;justify-content:center;}
    .gauge svg{display:block;}
    .gauge-label{font-size:10px;color:#8b949e;letter-spacing:.1em;text-transform:uppercase;}
    .gauge-empty{width:104px;height:104px;border-radius:50%;border:8px solid #2a1a3d;
      display:flex;align-items:center;justify-content:center;}
    .gauge-num{font-size:22px;color:#6e7681;font-family:'JetBrains Mono',monospace;}

    /* Табы-пилюли с циан-подсветкой активной */
    .stTabs [data-baseweb="tab"]{border-radius:8px 8px 0 0!important;}
    .stTabs [aria-selected="true"]{
      background:linear-gradient(180deg, rgba(191,95,255,.14), transparent)!important;
      border-bottom:2px solid #22d3ee!important;color:#d9a6ff!important;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="spider-wrap">
      <svg style="position:absolute;top:0;right:0;width:160px;height:160px" viewBox="0 0 160 160">
        <line x1="160" y1="0" x2="0" y2="0" stroke="#bf5fff" stroke-width="0.5" opacity="0.5"/>
        <line x1="160" y1="0" x2="160" y2="160" stroke="#bf5fff" stroke-width="0.5" opacity="0.5"/>
        <line x1="160" y1="0" x2="30" y2="160" stroke="#bf5fff" stroke-width="0.4" opacity="0.3"/>
        <path d="M130 0 Q160 0 160 30" stroke="#bf5fff" stroke-width="0.5" fill="none" opacity="0.4"/>
        <path d="M90 0 Q160 0 160 70" stroke="#bf5fff" stroke-width="0.4" fill="none" opacity="0.3"/>
      </svg>
      <div class="spider-thread"></div>
      <div class="spider">🕷️</div>
    </div>
    """, unsafe_allow_html=True)
