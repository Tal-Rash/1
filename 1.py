import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП Cloud", layout="wide")

# Ссылка на вашу таблицу
URL = "https://docs.google.com/spreadsheets/d/1HYkcxtOiEhV7-jOi6TGDxT-exQv78guO9g7b4JVBxAc/edit?usp=sharing"

# 2. Подключение
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # Читаем Sheet1. ttl=0 отключает кэширование старых ошибок.
        df = conn.read(spreadsheet=URL, worksheet="Sheet1", ttl=0)
        if df is not None and not df.empty:
            # Оставляем только нужные колонки, игнорируя пустые "Unnamed"
            cols = ["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"]
            return df[cols]
        return pd.DataFrame(columns=["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"])
    except:
        # Если любая ошибка (включая 0), возвращаем пустой каркас
        return pd.DataFrame(columns=["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"])

# 3. Красивый CSS
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; max-width: 98% !important; }
        h1 { font-size: 1.8rem !important; color: #1e3a8a; border-bottom: 2px solid #1e3a8a; margin-bottom: 1rem !important; }
        div.stButton > button { 
            background-color: #10b981 !important; 
            color: white !important; 
            font-weight: bold !important; 
            width: 100%; height: 3.5em; border-radius: 10px; 
        }
    </style>
    """, unsafe_allow_html=True)

st.title("🚂 ОБЛАЧНЫЙ УЧЕТ ПАРАМЕТРОВ КП")

# Поля ввода
c1, c2, _ = st.columns([2, 2, 6])
loco = c1.text_input("📝 № Локомотива", key="loco_input")
date_m = c2.date_input("📅 Дата замера", datetime.now())

# Логика осей
axes_count = 12 if len(loco) == 2 else 6
st.write(f"#### Сетка замера ({axes_count} осей)")

cols_name = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols_name)

edited_df = st.data_editor(df_template, width="stretch", height=400 if axes_count == 12 else 260)

if st.button("📥 СОХРАНИТЬ В GOOGLE ТАБЛИЦУ"):
    if not loco:
        st.error("❗ Ошибка: Введите номер локомотива")
    else:
        with st.status("⏳ Запись в облако...") as status:
            try:
                # 1. Читаем старые данные
                old_df = get_data()
                
                # 2. Собираем новые строки
                new_rows = []
                for i, (idx, row) in enumerate(edited_df.iterrows(), start=1):
                    new_rows.append({
                        "Дата": date_m.strftime("%d.%m.%Y"), "Локо": loco, "Ось": i,
                        "Гр_Л": row[0], "Гр_П": row[1], "Пр_Л": row[2], "Пр_П": row[3],
                        "qR_Л": row[4], "qR_П": row[5], "Банд_Л": row[6], "Банд_П": row[7]
                    })
                new_df = pd.DataFrame(new_rows)
                
                # 3. Объединяем
                final_df = pd.concat([old_df, new_df], ignore_index=True)
                
                # 4. Финальная очистка структуры перед отправкой
                columns_order = ["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"]
                final_df = final_df[columns_order]
                
                # 5. Запись
                conn.update(spreadsheet=URL, worksheet="Sheet1", data=final_df)
                
                status.update(label="✅ Данные успешно сохранены!", state="complete")
                st.balloons()
            except Exception as e:
                status.update(label="❌ Ошибка", state="error")
                st.error(f"Детально: {e}")

# Вкладка архива
if st.checkbox("Показать архив замеров"):
    st.dataframe(get_data(), width="stretch")
