import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. Настройка страницы (обязательно первой)
st.set_page_config(page_title="Учет КП", layout="wide")

# 2. Подключение базы данных
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

# 3. Интерфейс
st.title("📱 Мобильный учет замеров КП")

tab1, tab2 = st.tabs(["📥 Ввод данных", "🗄️ Архив"])

with tab1:
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        loco = col1.text_input("Локомотив", placeholder="Например: 123")
        date_m = col2.date_input("Дата", datetime.now())
        
        # Определяем кол-во осей по длине номера (как в вашем коде)
        axes_count = 12 if len(loco) == 2 else 6
        st.write(f"Заполнение для **{axes_count}** осей")
        
        all_data = []
        for i in range(1, axes_count + 1):
            with st.expander(f"Ось №{i}", expanded=(i==1)):
                c1, c2, c3, c4 = st.columns(4)
                fl = c1.number_input(f"Гр. Л", step=0.1, key=f"fl{i}")
                fr = c2.number_input(f"Гр. П", step=0.1, key=f"fr{i}")
                wl = c3.number_input(f"Пр. Л", step=0.1, key=f"wl{i}")
                wr = c4.number_input(f"Пр. П", step=0.1, key=f"wr{i}")
                
                # Добавляем в список для сохранения
                all_data.append((loco, i, fl, fr, wl, wr, 0.0, 0.0, 0.0, 0.0, date_m.strftime("%d.%m.%Y")))
        
        if st.form_submit_button("✅ СОХРАНИТЬ В БАЗУ", use_container_width=True):
            if not loco:
                st.error("Укажите номер локомотива!")
            else:
                cur = conn.cursor()
                cur.executemany("INSERT INTO measurements (loco_name, wheel_num, f_l, f_r, w_l, w_r, q_l, q_r, t_l, t_r, date) VALUES (?,?,?,?,?,?,?,?,?,?,?)", all_data)
                conn.commit()
                st.success(f"Данные по {loco} сохранены!")

with tab2:
    st.subheader("Последние записи")
    df = pd.read_sql("SELECT date, loco_name, wheel_num, f_l, f_r, w_l, w_r FROM measurements ORDER BY id DESC LIMIT 100", conn)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Архив пока пуст.")
