import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП v40.2", layout="wide")

# 2. Оптимизированный CSS для компактности
st.markdown("""
    <style>
        /* Максимально используем высоту экрана */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            max-width: 98% !important;
        }
        
        /* Компактный заголовок */
        h1 {
            font-size: 1.8rem !important;
            margin-bottom: 0.5rem !important;
            border-bottom: 2px solid #1e3a8a;
        }

        /* Делаем вкладки ниже, чтобы сэкономить место */
        .stTabs [data-baseweb="tab-list"] {
            gap: 5px;
            padding: 0px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 40px !important;
            padding: 0px 20px !important;
        }

        /* Уменьшаем шрифты в полях ввода */
        .stTextInput label, .stDateInput label {
            font-size: 0.9rem !important;
            margin-bottom: 0px !important;
        }

        /* ГЛАВНОЕ: Компактность таблицы st.data_editor */
        [data-testid="stDataEditor"] div {
            font-size: 0.85rem !important;
        }
        
        /* Уменьшаем межстрочный интервал в самой таблице */
        div[data-testid="stDataEditor"] > div:nth-child(2) {
            height: auto !important;
            max-height: 65vh !important; /* Таблица займет 65% высоты экрана */
        }

        /* Кнопка сохранения компактнее */
        div.stButton > button {
            height: 2.5em !important;
            margin-top: 10px !important;
        }
    </style>
    """, unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect("wheels_data.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS measurements 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      loco_name TEXT, wheel_num INTEGER, 
                      f_l REAL, f_r REAL, w_l REAL, w_r REAL, 
                      q_l REAL, q_r REAL, t_l REAL, t_r REAL, date TEXT)''')
    conn.commit()
    return conn

conn = init_db()

st.title("🚂 УЧЕТ ПАРАМЕТРОВ КОЛЕСНЫХ ПАР")

tab_input, tab_archive, tab_analysis = st.tabs(["📥 ВВОД", "🗄️ АРХИВ", "📊 АНАЛИЗ"])

# --- ВКЛАДКА: ВВОД ДАННЫХ ---
with tab_input:
    c1, c2, _ = st.columns([2, 2, 6])
    loco = c1.text_input("📝 № Локомотива", placeholder="Введите №", key="loco_nr")
    date_m = c2.date_input("📅 Дата", datetime.now())

    # Логика количества осей
    axes_count = 12 if len(loco) == 2 else 6

    # Сетка замера
    cols_name = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
    df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols_name)

    # Редактор таблицы с фиксированной высотой, чтобы все оси влезли
    edited_df = st.data_editor(
        df_template, 
        use_container_width=True, 
        key=f"ed_{axes_count}_{loco}",
        # Устанавливаем высоту так, чтобы 12 осей помещались без прокрутки страницы
        height=450 if axes_count == 12 else 250,
        column_config={c: st.column_config.NumberColumn(format="%.1f", width="small") for c in cols_name}
    )

    if st.button("📥 СОХРАНИТЬ В БАЗУ", use_container_width=True):
        if not loco:
            st.error("❗ Укажите номер локомотива")
        else:
            data = []
            for i, (idx, row) in enumerate(edited_df.iterrows(), start=1):
                data.append((loco, i, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], date_m.strftime("%d.%m.%Y")))
            
            cur = conn.cursor()
            cur.executemany("INSERT INTO measurements (loco_name, wheel_num, f_l, f_r, w_l, w_r, q_l, q_r, t_l, t_r, date) VALUES (?,?,?,?,?,?,?,?,?,?,?)", data)
            conn.commit()
            st.success(f"✅ Данные по {loco} ({axes_count} осей) сохранены!")

# Остальные вкладки (Архив и Анализ) остаются без изменений
with tab_archive:
    # ... (код архива из предыдущего ответа)
    pass
