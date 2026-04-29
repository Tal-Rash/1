import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Учет КП Cloud", layout="wide")

# Ссылка на таблицу
URL = "https://docs.google.com/spreadsheets/d/1HYkcxtOiEhV7-jOi6TGDxT-exQv78guO9g7b4JVBxAc/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # Пробуем прочитать Sheet1. TTL=0 отключает кэш.
        df = conn.read(spreadsheet=URL, worksheet="Sheet1", ttl=0)
        if df is not None and not df.empty:
            return df
        return pd.DataFrame(columns=["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"])
    except:
        # Если получаем ошибку 0, возвращаем пустую структуру
        return pd.DataFrame(columns=["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"])

st.title("🚂 СИСТЕМА УЧЕТА КП")

# Поля ввода
c1, c2 = st.columns(2)
loco = c1.text_input("№ Локомотива")
date_m = c2.date_input("Дата", datetime.now())

axes = 12 if len(loco) == 2 else 6
cols = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
df_edit = st.data_editor(pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes)], columns=cols), width="stretch")

if st.button("📥 СОХРАНИТЬ В ОБЛАКО"):
    if not loco:
        st.error("Введите номер локомотива!")
    else:
        try:
            # Читаем текущее состояние
            old_df = get_data()
            
            # Собираем новые строки
            new_rows = []
            for i, (idx, row) in enumerate(df_edit.iterrows(), start=1):
                new_rows.append({
                    "Дата": date_m.strftime("%d.%m.%Y"), "Локо": loco, "Ось": i,
                    "Гр_Л": row[0], "Гр_П": row[1], "Пр_Л": row[2], "Пр_П": row[3],
                    "qR_Л": row[4], "qR_П": row[5], "Банд_Л": row[6], "Банд_П": row[7]
                })
            
            new_df = pd.DataFrame(new_rows)
            
            # Склеиваем и УДАЛЯЕМ лишние колонки, которые плодит Google
            final_df = pd.concat([old_df, new_df], ignore_index=True)
            final_df = final_df[["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"]]
            
            # Запись
            conn.update(spreadsheet=URL, worksheet="Sheet1", data=final_df)
            st.success("Данные успешно сохранены!")
            st.balloons()
        except Exception as e:
            st.error(f"Ошибка: {e}")
