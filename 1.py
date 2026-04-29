import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП v40.8", layout="wide")

# --- ВАША АКТУАЛЬНАЯ ССЫЛКА ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyv8DGdv9wtVy7bAtvwjzm9J5s88TDXd8nnaDNBG29G74zRlL6Z2gh0hUQ2Dsb-qGux/exec"

# Ссылка для чтения (архива)
SHEET_ID = "1HYkcxtOiEhV7-jOi6TGDxT-exQv78guO9g7b4JVBxAc"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# 2. Оформление интерфейса
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

st.title("🚂 СИСТЕМА УЧЕТА КП")

# 3. Ввод данных
c1, c2, _ = st.columns([2, 2, 6])
loco = c1.text_input("📝 № Локомотива", key="loco_input")
date_m = c2.date_input("📅 Дата замера", datetime.now())

# Автоматический выбор количества осей
axes_count = 12 if len(loco) == 2 else 6
st.write(f"#### Сетка замера ({axes_count} осей)")

cols_name = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols_name)

edited_df = st.data_editor(df_template, width="stretch", height=400 if axes_count == 12 else 260)

st.markdown("---")

# 4. Логика отправки
if st.button("📥 ОТПРАВИТЬ ДАННЫЕ В ОБЛАКО"):
    if not loco:
        st.error("❗ Ошибка: Введите номер локомотива")
    else:
        with st.spinner("🚀 Отправка данных в Google..."):
            try:
                # Подготовка данных
                payload = []
                for i, (idx, row) in enumerate(edited_df.iterrows(), start=1):
                    payload.append([
                        date_m.strftime("%d.%m.%Y"), 
                        loco, 
                        i,
                        row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]
                    ])
                
                # Отправка с принудительным следованием по редиректам
                response = requests.post(
                    SCRIPT_URL, 
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    allow_redirects=True,
                    timeout=30
                )
                
                # Проверка результата
                if response.status_code in [200, 302]:
                    st.success("✅ Данные успешно записаны в Google Таблицу!")
                    st.balloons()
                else:
                    st.error(f"❌ Ошибка связи: Код {response.status_code}")
                    st.write("Ответ сервера:", response.text)
                    
            except Exception as e:
                st.error(f"❌ Ошибка связи: {e}")
                st.info("Попробуйте обновить страницу или проверить соединение.")

# 5. Архив
if st.checkbox("🔍 Показать архив"):
    try:
        df_view = pd.read_csv(CSV_URL)
        st.dataframe(df_view.tail(24), width="stretch")
    except:
        st.info("Архив пока недоступен или пуст.")
