import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Настройка страницы
st.set_page_config(page_title="Учет КП: Полная версия", layout="wide")

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

# Создаем вкладки (как в версии для Windows)
tab_input, tab_archive, tab_analysis = st.tabs(["📥 Ввод данных", "🗄️ Архив замеров", "📊 Анализ износа"])

# --- ВКЛАДКА: ВВОД ДАННЫХ ---
with tab_input:
    col1, col2 = st.columns(2)
    loco = col1.text_input("Номер локомотива", key="input_loco")
    date_m = col2.date_input("Дата замера", datetime.now(), key="input_date")

    axes_count = 12 if len(loco) == 2 else 6
    
    st.write(f"### Таблица замера ({axes_count} осей)")
    
    # Подготовка пустой таблицы для ввода
    cols = ["Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"]
    df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols)

    edited_df = st.data_editor(df_template, use_container_width=True, key="editor")

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
            st.success(f"Замеры по локомотиву {loco} за {date_m.strftime('%d.%m.%Y')} сохранены!")

# --- ВКЛАДКА: АРХИВ ЗАМЕРОВ ---
with tab_archive:
    st.subheader("🔎 Поиск и просмотр истории")
    
    # Загружаем список всех локомотивов для фильтра
    all_locos = pd.read_sql("SELECT DISTINCT loco_name FROM measurements", conn)["loco_name"].tolist()
    
    col_f1, col_f2 = st.columns([1, 2])
    filter_loco = col_f1.selectbox("Фильтр по локомотиву", ["Все"] + all_locos)
    
    # Формируем SQL запрос в зависимости от фильтра
    query = "SELECT date as 'Дата', loco_name as 'Локо', wheel_num as 'Ось', f_l as 'Гр_Л', f_r as 'Гр_П', w_l as 'Пр_Л', w_r as 'Пр_П', q_l as 'qR_Л', q_r as 'qR_П', t_l as 'Банд_Л', t_r as 'Банд_П' FROM measurements"
    if filter_loco != "Все":
        query += f" WHERE loco_name = '{filter_loco}'"
    query += " ORDER BY id DESC"
    
    df_archive = pd.read_sql(query, conn)
    
    if not df_archive.empty:
        # Позволяем скачивать архив в Excel
        st.download_button("💾 Скачать архив (CSV)", df_archive.to_csv(index=False).encode('utf-8-sig'), "archive_wheels.csv", "text/csv")
        st.dataframe(df_archive, use_container_width=True, height=600)
    else:
        st.info("В базе данных пока нет записей.")

# --- ВКЛАДКА: АНАЛИЗ ИЗНОСА ---
with tab_analysis:
    st.subheader("📉 Сравнение замеров")
    if not all_locos:
        st.info("Нет данных для анализа.")
    else:
        target_loco = st.selectbox("Выберите локомотив для анализа", all_locos, key="analysis_loco")
        df_loco = pd.read_sql(f"SELECT * FROM measurements WHERE loco_name = '{target_loco}' ORDER BY date ASC", conn)
        
        dates = df_loco['date'].unique()
        if len(dates) < 2:
            st.warning("Для анализа нужно минимум 2 замера в разные даты.")
        else:
            st.write(f"Найдено замеров: {len(dates)}")
            st.dataframe(df_loco, use_container_width=True)
