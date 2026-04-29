import streamlit as st
import pandas as pd
import json
import urllib.parse
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП v50.1", layout="wide")

# --- ВАША ССЫЛКА ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyYLMw1smqeKRHZQFZsV35k2RqkR6bTmR1TiYPeSbYiVDb3KyGonYmdS7FohfxeCGKT/exec"

# Ссылка для архива (чтение)
SHEET_ID = "1HYkcxtOiEhV7-jOi6TGDxT-exQv78guO9g7b4JVBxAc"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# 2. Стиль
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; max-width: 98% !important; }
        h1 { font-size: 1.8rem !important; color: #1e3a8a; border-bottom: 2px solid #1e3a8a; }
        .send-button {
            display: block;
            text-align: center;
            background-color: #10b981;
            color: white !important;
            padding: 20px;
            text-decoration: none;
            font-size: 22px;
            font-weight: bold;
            border-radius: 12px;
            margin-top: 20px;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
            transition: 0.3s;
        }
        .send-button:hover { background-color: #059669; transform: translateY(-2px); }
    </style>
    """, unsafe_allow_html=True)

st.title("🚂 СИСТЕМА УЧЕТА КП")

# 3. Ввод данных
c1, c2, _ = st.columns([2, 2, 6])
loco = c1.text_input("📝 № Локомотива", key="loco_input")
date_m = c2.date_input("📅 Дата замера", datetime.now())

axes_count = 12 if len(loco) == 2 else 6
st.write(f"#### Сетка замера ({axes_count} осей)")

# Названия колонок (должны точно совпадать)
cols_name = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols_name)

# Редактор таблицы
edited_df = st.data_editor(df_template, width="stretch", height=400 if axes_count == 12 else 260)

# 4. Формирование ссылки (ИСПРАВЛЕННЫЙ БЛОК)
payload = []
for i, (idx, row) in enumerate(edited_df.iterrows(), start=1):
    payload.append([
        date_m.strftime("%d.%m.%Y"), 
        loco, 
        i,
        row["Гр Л"], row["Гр П"], 
        row["Пр Л"], row["Пр П"], 
        row["qR Л"], row["qR П"], 
        row["Банд Л"], row["Банд П"]
    ])

json_data = json.dumps(payload)
params = urllib.parse.quote(json_data)
final_link = f"{SCRIPT_URL}?data={params}"

st.markdown("---")

# 5. Кнопка отправки
if loco:
    st.markdown(f'<a href="{final_link}" target="_blank" class="send-button">🚀 ПОДТВЕРДИТЬ И ОТПРАВИТЬ В GOOGLE</a>', unsafe_allow_html=True)
    st.info("💡 После нажатия откроется новая вкладка. Если увидите 'Success', значит данные в таблице.")
else:
    st.warning("⚠️ Введите номер локомотива.")

# 6. Архив
if st.checkbox("🔍 Показать архив"):
    try:
        df_view = pd.read_csv(CSV_URL)
        st.dataframe(df_view.tail(20), width="stretch")
    except:
        st.info("Архив пока пуст.")
