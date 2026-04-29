import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП: Полная версия", layout="wide")

# 2. CSS для изменения высоты и размера заголовков/вкладок
st.markdown("""
    <style>
        /* Убираем лишний отступ сверху страницы */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }
        
        /* Увеличиваем главный заголовок */
        h1 {
            font-size: 2.5rem !important;
            margin-bottom: 1rem !important;
            padding-top: 0rem !important;
        }

        /* Стилизация вкладок (Tabs) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 60px; /* Делаем вкладки выше */
            background-color: #f0f2f6;
            border-radius: 5px 5px 0px 0px;
            gap: 1px;
            padding-left: 20px;
            padding-right: 20px;
        }

        /* Размер шрифта внутри вкладок */
        .stTabs [data-baseweb="tab"] p {
            font-size: 20px;
            font-weight: bold;
        }

        /* Цвет активной вкладки */
        .stTabs [aria-selected="true"] {
            background-color: #4CAF50 !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Инициализация базы данных
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

st.title("🚂 Система учета параметров КП")

# Создаем вкладки
tab_input, tab_archive, tab_analysis = st.tabs(["📥 Ввод данных", "🗄️ Архив замеров", "📊 Анализ износа"])

# --- ВКЛАДКА: ВВОД ДАННЫХ ---
with tab_input:
    col1, col2 = st.columns(2)
    loco = col1.text_input("Номер локомотива", key="input_loco")
    date_m = col2.date_input("Дата замера", datetime.now(), key="input_date")

    # Условие по количеству колес
    if len(loco) == 2:
        axes_count = 12
    else:
        axes_count = 6

    st.markdown(f"### 📋 Таблица замера ({axes_count} осей)")
    
    cols = ["Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"]
    df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols)

    edited_df = st.data_editor(df_template, use_container_width=True, key=f"ed_{axes_count}_{loco}")

    if st.button("📥 СОХРАНИТЬ В БАЗУ", use_container_width=True):
        if not loco:
            st.error("Введите номер локомотива!")
        else:
            data = []
            for i, (idx, row) in enumerate(edited_df.iterrows(), start=1):
                data.append((loco, i, row["Гр_Л"], row["Гр_П"], row["Пр_Л"], row["Пр_П"], 
                             row["qR_Л"], row["qR_П"], row["Банд_Л"], row["Банд_П"], 
                             date_m.strftime("%d.%m.%Y")))
            
            cur = conn.cursor()
            cur.executemany("INSERT INTO measurements (loco_name, wheel_num, f_l, f_r, w_l, w_r, q_l, q_r, t_l, t_r, date) VALUES (?,?,?,?,?,?,?,?,?,?,?)", data)
            conn.commit()
            st.success(f"Замеры по локомотиву {loco} сохранены!")

# --- ВКЛАДКА: АРХИВ ЗАМЕРОВ ---
with tab_archive:
    st.subheader("🔎 Поиск и просмотр истории")
    
    all_locos_df = pd.read_sql("SELECT DISTINCT loco_name FROM measurements", conn)
    all_locos = all_locos_df["loco_name"].tolist() if not all_locos_df.empty else []
    
    col_f1, col_f2 = st.columns([1, 2])
    filter_loco = col_f1.selectbox("Фильтр по локомотиву", ["Все"] + all_locos)
    
    query = "SELECT date as 'Дата', loco_name as 'Локо', wheel_num as 'Ось', f_l as 'Гр_Л', f_r as 'Гр_П', w_l as 'Пр_Л', w_r as 'Пр_П', q_l as 'qR_Л', q_r as 'qR_П', t_l as 'Банд_Л', t_r as 'Банд_П' FROM measurements"
    if filter_loco != "Все":
        query += f" WHERE loco_name = '{filter_loco}'"
    query += " ORDER BY id DESC"
    
    df_archive = pd.read_sql(query, conn)
    st.dataframe(df_archive, use_container_width=True, height=600)

# --- ВКЛАДКА: АНАЛИЗ ИЗНОСА ---
with tab_analysis:
    st.subheader("📊 Анализ")
    st.info("Раздел в разработке.")
