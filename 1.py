import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП v40.7", layout="wide")

# --- ВАША НОВАЯ ССЫЛКА ИНТЕГРИРОВАНА ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwhvCHgy-R5hgzeSurDFA7HPb8D4hQrdcITHeUcuPxa5fzx2BSVZXIWGyg9wZtrjQHL/exec"

# Ссылка для чтения архива (через экспорт CSV)
SHEET_ID = "1HYkcxtOiEhV7-jOi6TGDxT-exQv78guO9g7b4JVBxAc"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# 2. Стиль интерфейса
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

st.title("🚂 СИСТЕМА УЧЕТА КП (v40.7)")

# 3. Блок ввода
c1, c2, _ = st.columns([2, 2, 6])
loco = c1.text_input("📝 № Локомотива", placeholder="Введите номер", key="loco_input")
date_m = c2.date_input("📅 Дата замера", datetime.now())

# Определение количества осей (2 знака = 12 осей, иначе 6)
axes_count = 12 if len(loco) == 2 else 6
st.write(f"#### Сетка замера ({axes_count} осей)")

cols_name = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols_name)

# Редактор таблицы
edited_df = st.data_editor(df_template, width="stretch", height=400 if axes_count == 12 else 260)

st.markdown("---")

# 4. Логика отправки через requests
if st.button("📥 СОХРАНИТЬ В GOOGLE ТАБЛИЦУ"):
    if not loco:
        st.error("❗ Ошибка: Введите номер локомотива")
    else:
        with st.spinner("🚀 Синхронизация с облаком..."):
            try:
                # Подготавливаем данные
                payload = []
                for i, (idx, row) in enumerate(edited_df.iterrows(), start=1):
                    payload.append([
                        date_m.strftime("%d.%m.%Y"), 
                        loco, 
                        i,
                        row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]
                    ])
                
                # Отправка POST-запроса с принудительным JSON-форматом
                response = requests.post(
                    SCRIPT_URL, 
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=20
                )
                
                # Проверка успешности (Google Apps Script часто возвращает 200 даже при ошибках в JS, 
                # поэтому проверяем текст ответа, если вы добавили return 'Success')
                if response.status_code == 200:
                    st.success("✅ Данные успешно добавлены в таблицу!")
                    st.balloons()
                else:
                    st.error(f"❌ Ошибка сервера Google: {response.status_code}")
                    st.write("Технический ответ:", response.text)
            except Exception as e:
                st.error(f"❌ Критическая ошибка соединения: {e}")
                st.info("Убедитесь, что вы опубликовали Apps Script с доступом 'Anyone' (Все).")

# 5. Просмотр архива
st.markdown("### 🗄️ Последние записи в таблице")
if st.checkbox("Показать архив"):
    try:
        df_view = pd.read_csv(CSV_URL)
        st.dataframe(df_view.tail(20), width="stretch")
    except:
        st.info("Для просмотра архива таблица не должна быть пустой.")
