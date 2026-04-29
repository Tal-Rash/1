import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Учет КП: Табличный ввод", layout="wide")

# Инициализация базы
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

st.title("📟 Табличный ввод замеров КП")

# Верхняя панель (как в Windows версии)
col1, col2, col3 = st.columns([2, 2, 4])
loco = col1.text_input("Локомотив", placeholder="Номер")
date_m = col2.date_input("Дата замера", datetime.now())

# Авто-определение количества осей
axes_count = 12 if len(loco) == 2 else 6

# Создаем пустую таблицу (DataFrame) для ввода
columns = ["Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"]
df_input = pd.DataFrame(
    0.0, 
    index=[f"Ось {i+1}" for i in range(axes_count)], 
    columns=columns
)

st.write(f"### Заполните таблицу для {axes_count} осей:")

# РЕДАКТОР ТАБЛИЦЫ (Аналог сетки из Tkinter)
edited_df = st.data_editor(
    df_input,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        col: st.column_config.NumberColumn(format="%.1f") for col in columns
    }
)

# Кнопка сохранения
if st.button("📥 СОХРАНИТЬ ВСЮ ТАБЛИЦУ В БАЗУ", use_container_width=True):
    if not loco:
        st.error("Ошибка: Не введен номер локомотива!")
    else:
        try:
            # Превращаем таблицу в список строк для базы данных
            data_to_save = []
            for i, (idx, row) in enumerate(edited_df.iterrows(), start=1):
                data_to_save.append((
                    loco, i, 
                    row["Гр_Л"], row["Гр_П"], 
                    row["Пр_Л"], row["Пр_П"], 
                    row["qR_Л"], row["qR_П"], 
                    row["Банд_Л"], row["Банд_П"], 
                    date_m.strftime("%d.%m.%Y")
                ))
            
            cur = conn.cursor()
            cur.executemany('''INSERT INTO measurements 
                               (loco_name, wheel_num, f_l, f_r, w_l, w_r, q_l, q_r, t_l, t_r, date) 
                               VALUES (?,?,?,?,?,?,?,?,?,?,?)''', data_to_save)
            conn.commit()
            st.success(f"Данные по локомотиву {loco} успешно сохранены в облачную базу!")
        except Exception as e:
            st.error(f"Ошибка при сохранении: {e}")

# Просмотр последних записей ниже
st.divider()
st.subheader("📋 Последние 10 записей из базы")
history_df = pd.read_sql("SELECT date, loco_name, wheel_num, f_l, f_r FROM measurements ORDER BY id DESC LIMIT 10", conn)
st.table(history_df)
