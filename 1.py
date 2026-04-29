import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Учет КП", layout="centered")

# Инициализация базы (в облаке создастся временный файл)
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

st.title("📊 Система учета замеров")

# Вкладки для мобильного удобства
tab1, tab2 = st.tabs(["📥 Ввод", "📜 Архив"])

with tab1:
    loco = st.text_input("Номер локомотива")
    date_m = st.date_input("Дата", datetime.now())
    
    axes = 12 if len(loco) == 2 else 6
    
    all_data = []
    for i in range(1, axes + 1):
        with st.expander(f"Ось №{i}"):
            c1, c2 = st.columns(2)
            fl = c1.number_input(f"Гребень Л ({i})", step=0.1, key=f"fl{i}")
            fr = c2.number_input(f"Гребень П ({i})", step=0.1, key=f"fr{i}")
            # ... здесь можно добавить остальные поля (прокат, qR) по аналогии
            all_data.append((loco, i, fl, fr, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, date_m.strftime("%d.%m.%Y")))

    if st.button("Сохранить"):
        cur = conn.cursor()
        cur.executemany("INSERT INTO measurements (loco_name, wheel_num, f_l, f_r, w_l, w_r, q_l, q_r, t_l, t_r, date) VALUES (?,?,?,?,?,?,?,?,?,?,?)", all_data)
        conn.commit()
        st.success("Готово!")

with tab2:
    df = pd.read_sql("SELECT * FROM measurements", conn)
    st.dataframe(df)
