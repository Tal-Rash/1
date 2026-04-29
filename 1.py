import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП v40.2", layout="wide")

# 2. Улучшенный CSS (Дизайн "Professional Dark/Light")
st.markdown("""
    <style>
        /* Общий фон и отступы */
        .main {
            background-color: #f8f9fa;
        }
        .block-container {
            padding-top: 1.5rem !important;
            max-width: 95% !important;
        }
        
        /* Заголовок */
        h1 {
            color: #1e3a8a;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 800;
            border-bottom: 3px solid #1e3a8a;
            padding-bottom: 10px;
            margin-bottom: 25px !important;
        }

        /* Красивые вкладки */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #e2e8f0;
            padding: 8px 8px 0px 8px;
            border-radius: 10px 10px 0px 0px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            background-color: #f1f5f9;
            border-radius: 8px 8px 0px 0px;
            padding: 0px 30px;
            border: 1px solid #cbd5e1;
            transition: all 0.3s;
        }

        .stTabs [data-baseweb="tab"]:hover {
            background-color: #ffffff;
            border-color: #1e3a8a;
        }

        .stTabs [aria-selected="true"] {
            background-color: #1e3a8a !important;
            color: white !important;
            box-shadow: 0px -4px 10px rgba(0,0,0,0.1);
        }

        /* Стилизация полей ввода */
        .stTextInput input, .stDateInput input {
            border: 2px solid #cbd5e1 !important;
            border-radius: 8px !important;
            padding: 10px !important;
            font-weight: 600;
        }

        /* Кнопка СОХРАНИТЬ */
        div.stButton > button {
            background-color: #10b981 !important;
            color: white !important;
            font-size: 18px !important;
            font-weight: bold !important;
            border-radius: 10px !important;
            height: 3em !important;
            border: none !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }
        
        div.stButton > button:hover {
            transform: translateY(-2px);
            background-color: #059669 !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
        }

        /* Подсветка секции таблицы */
        .stDataEditor {
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
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

st.title("🚂 УЧЕТ ПАРАМЕТРОВ КОЛЕСНЫХ ПАР")

tab_input, tab_archive, tab_analysis = st.tabs(["📥 ВВОД ДАННЫХ", "🗄️ АРХИВ ЗАМЕРОВ", "📊 АНАЛИЗ ИЗНОСА"])

# --- ВКЛАДКА: ВВОД ДАННЫХ ---
with tab_input:
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 3])
        loco = col1.text_input("📝 Номер локомотива", placeholder="Введите №")
        date_m = col2.date_input("📅 Дата замера", datetime.now())

        # Логика количества осей
        if len(loco) == 2:
            axes_count = 12
        elif len(loco) >= 3:
            axes_count = 6
        else:
            axes_count = 6

        st.markdown(f"#### 🛠️ Сетка замера для локомотива № {loco if loco else '...'}")
        
        cols_name = ["Гребень Л", "Гребень П", "Прокат Л", "Прокат П", "qR Л", "qR П", "Бандаж Л", "Бандаж П"]
        df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols_name)

        # Редактор таблицы с настройкой точности
        edited_df = st.data_editor(
            df_template, 
            use_container_width=True, 
            key=f"ed_{axes_count}_{loco}",
            column_config={c: st.column_config.NumberColumn(format="%.1f") for c in cols_name}
        )

        st.markdown("<br>", unsafe_allow_html=True) # Отступ
        if st.button("📥 СОХРАНИТЬ РЕЗУЛЬТАТЫ В БАЗУ", use_container_width=True):
            if not loco:
                st.error("❗ Ошибка: Укажите номер локомотива")
            else:
                data = []
                for i, (idx, row) in enumerate(edited_df.iterrows(), start=1):
                    data.append((loco, i, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], date_m.strftime("%d.%m.%Y")))
                
                cur = conn.cursor()
                cur.executemany("INSERT INTO measurements (loco_name, wheel_num, f_l, f_r, w_l, w_r, q_l, q_r, t_l, t_r, date) VALUES (?,?,?,?,?,?,?,?,?,?,?)", data)
                conn.commit()
                st.success(f"✅ Данные по локомотиву {loco} ({axes_count} осей) успешно записаны!")

# --- ВКЛАДКА: АРХИВ ЗАМЕРОВ ---
with tab_archive:
    st.markdown("### 🔍 Просмотр истории базы данных")
    
    # Список для фильтра
    all_locos_df = pd.read_sql("SELECT DISTINCT loco_name FROM measurements", conn)
    all_locos = all_locos_df["loco_name"].tolist() if not all_locos_df.empty else []
    
    col_f1, col_f2 = st.columns([2, 5])
    filter_loco = col_f1.selectbox("Выбор локомотива", ["Показать все"] + all_locos)
    
    query = "SELECT date as 'Дата', loco_name as 'Локо', wheel_num as 'Ось', f_l as 'Гр_Л', f_r as 'Гр_П', w_l as 'Пр_Л', w_r as 'Пр_П', q_l as 'qR_Л', q_r as 'qR_П', t_l as 'Банд_Л', t_r as 'Банд_П' FROM measurements"
    if filter_loco != "Показать все":
        query += f" WHERE loco_name = '{filter_loco}'"
    query += " ORDER BY id DESC"
    
    df_archive = pd.read_sql(query, conn)
    
    if not df_archive.empty:
        st.dataframe(df_archive, use_container_width=True, height=550)
        st.download_button("📂 Выгрузить в CSV для Excel", df_archive.to_csv(index=False).encode('utf-8-sig'), "archive.csv", "text/csv")
    else:
        st.info("В базе данных пока пусто.")

# --- ВКЛАДКА: АНАЛИЗ ИЗНОСА ---
with tab_analysis:
    st.subheader("📊 Анализ параметров")
    st.write("Сравнение динамики износа будет доступно здесь.")
