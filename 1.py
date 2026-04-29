import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Настройка страницы
st.set_page_config(page_title="Учет КП 40.2 (Cloud)", layout="wide")

# Инициализация базы данных (в облаке)
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

# Цветовая индикация (логика из вашего последнего кода)
def get_color(param, val):
    limits = {
        "Гребень": {"yellow": 26.0, "red": 25.0, "mode": "min"},
        "Прокат": {"yellow": 5.0, "red": 7.0, "mode": "max"}
    }
    if param not in limits: return ""
    lim = limits[param]
    if lim["mode"] == "min":
        if val <= lim["red"]: return "background-color: #ff6666"
        if val <= lim["yellow"]: return "background-color: #ffff99"
    else:
        if val >= lim["red"]: return "background-color: #ff6666"
        if val >= lim["yellow"]: return "background-color: #ffff99"
    return ""

st.title("🚂 Учет КП: Версия 40.2 (Облачная)")

menu = st.sidebar.radio("Меню", ["Ввод данных", "Анализ износа", "Архив"])

if menu == "Ввод данных":
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        loco = col1.text_input("Локомотив")
        date_m = col2.date_input("Дата", datetime.now())
        
        axes = 12 if len(loco) == 2 else 6
        st.subheader(f"Ввод параметров для {axes} осей")
        
        all_rows = []
        for i in range(1, axes + 1):
            with st.expander(f"Ось №{i}"):
                c1, c2, c3, c4 = st.columns(4)
                fl = c1.number_input(f"Гр. Л ({i})", step=0.1, key=f"fl{i}")
                fr = c2.number_input(f"Гр. П ({i})", step=0.1, key=f"fr{i}")
                wl = c3.number_input(f"Пр. Л ({i})", step=0.1, key=f"wl{i}")
                wr = c4.number_input(f"Пр. П ({i})", step=0.1, key=f"wr{i}")
                all_rows.append((loco, i, fl, fr, wl, wr, 0.0, 0.0, 0.0, 0.0, date_m.strftime("%d.%m.%Y")))
        
        if st.form_submit_button("СОХРАНИТЬ"):
            cur = conn.cursor()
            cur.executemany("INSERT INTO measurements (loco_name, wheel_num, f_l, f_r, w_l, w_r, q_l, q_r, t_l, t_r, date) VALUES (?,?,?,?,?,?,?,?,?,?,?)", all_rows)
            conn.commit()
            st.success("Данные успешно добавлены!")

elif menu == "Анализ износа":
    st.subheader("📊 Анализ изменения параметров")
    loco_list = pd.read_sql("SELECT DISTINCT loco_name FROM measurements", conn)
    target = st.selectbox("Выберите локомотив", loco_list)
    
    if target:
        df = pd.read_sql(f"SELECT * FROM measurements WHERE loco_name='{target}' ORDER BY date ASC", conn)
        if len(df['date'].unique()) >= 2:
            st.write("Сравнение первого и последнего замеров:")
            st.dataframe(df) # Здесь можно добавить логику вычитания как в оригинале
        else:
            st.info("Недостаточно данных для анализа (нужно минимум 2 замера)")

elif menu == "Архив":
    st.subheader("🗄️ Все записи в базе")
    df_all = pd.read_sql("SELECT date, loco_name, wheel_num, f_l, f_r, w_l, w_r FROM measurements", conn)
    st.dataframe(df_all, use_container_width=True)
