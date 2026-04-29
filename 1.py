import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Учет КП v40.2 Cloud", layout="wide")

# Ссылка на вашу таблицу
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1HYkcxtOiEhV7-jOi6TGDxT-exQv78guO9g7b4JVBxAc/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def get_cloud_data():
    try:
        # Пробуем прочитать данные. Если таблица совсем новая, может выдать 0.
        return conn.read(spreadsheet=SPREADSHEET_URL, ttl=0)
    except:
        # Если ошибка 0 или любая другая при чтении — возвращаем пустой каркас
        return pd.DataFrame(columns=["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"])

st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; max-width: 98% !important; }
        h1 { font-size: 1.8rem !important; color: #1e3a8a; border-bottom: 2px solid #1e3a8a; }
        div.stButton > button { background-color: #10b981 !important; color: white !important; font-weight: bold !important; width: 100%; height: 3.5em; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚂 ОБЛАЧНЫЙ УЧЕТ ПАРАМЕТРОВ КП")

tab_input, tab_archive = st.tabs(["📥 ВВОД ДАННЫХ", "🗄️ АРХИВ"])

with tab_input:
    c1, c2, _ = st.columns([2, 2, 6])
    loco = c1.text_input("📝 № Локомотива", key="loco_input")
    date_m = c2.date_input("📅 Дата замера", datetime.now())

    axes_count = 12 if len(loco) == 2 else 6
    cols_name = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
    df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols_name)

    edited_df = st.data_editor(df_template, width="stretch", key=f"ed_{axes_count}_{loco}", height=400)

    if st.button("📥 ОТПРАВИТЬ В GOOGLE ТАБЛИЦУ"):
        if not loco:
            st.error("❗ Введите номер локомотива")
        else:
            try:
                # Читаем то, что есть (или получаем каркас)
                existing_df = get_cloud_data()
                
                # Готовим новые строки
                new_rows = []
                for i, (idx, row) in enumerate(edited_df.iterrows(), start=1):
                    new_rows.append({
                        "Дата": date_m.strftime("%d.%m.%Y"),
                        "Локо": loco,
                        "Ось": i,
                        "Гр_Л": row[0], "Гр_П": row[1],
                        "Пр_Л": row[2], "Пр_П": row[3],
                        "qR_Л": row[4], "qR_П": row[5],
                        "Банд_Л": row[6], "Банд_П": row[7]
                    })
                new_df = pd.DataFrame(new_rows)
                
                # Соединяем
                if existing_df.empty or len(existing_df.columns) < 5:
                    updated_df = new_df
                else:
                    # Очищаем старые данные от пустых строк перед склейкой
                    existing_df = existing_df.dropna(how='all')
                    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                
                # ЗАПИСЬ
                conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
                st.success("✅ Сохранено в Google!")
                st.balloons()
            except Exception as e:
                st.error(f"Ошибка: {e}")
                st.info("Попробуйте вписать заголовки в таблицу вручную и перезапустить приложение.")

with tab_archive:
    if st.button("🔄 Обновить архив"):
        st.dataframe(get_cloud_data(), width="stretch", height=500)
