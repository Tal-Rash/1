import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП Cloud", layout="wide")

# ВАША ССЫЛКА (экспортный формат)
# Мы меняем /edit на /export?format=csv, чтобы Pandas читал таблицу без ошибок
SHEET_ID = "1HYkcxtOiEhV7-jOi6TGDxT-exQv78guO9g7b4JVBxAc"
CSV_URL = f"https://script.google.com/macros/s/AKfycbzV--LB0W0TqIDsBqgSeLKbFe8InZLB6l3y25KkwanrgXVx53hRb-PPWKlh93WkFquQ/exec"

# Функция чтения через стандартный Pandas
def get_data():
    try:
        return pd.read_csv(CSV_URL)
    except:
        return pd.DataFrame(columns=["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"])

st.title("🚂 СИСТЕМА УЧЕТА КП (v.40.5)")

# Ввод данных
c1, c2 = st.columns(2)
loco = c1.text_input("📝 № Локомотива")
date_m = c2.date_input("📅 Дата", datetime.now())

axes = 12 if len(loco) == 2 else 6
cols = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
df_edit = st.data_editor(pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes)], columns=cols), width="stretch")

if st.button("📥 ОТПРАВИТЬ ДАННЫЕ"):
    if not loco:
        st.error("Введите номер локомотива!")
    else:
        with st.status("Отправка...") as status:
            try:
                # 1. Читаем текущие данные
                old_df = get_data()
                
                # 2. Формируем новые
                new_rows = []
                for i, (idx, row) in enumerate(df_edit.iterrows(), start=1):
                    new_rows.append([
                        date_m.strftime("%d.%m.%Y"), loco, i,
                        row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]
                    ])
                
                new_df = pd.DataFrame(new_rows, columns=["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"])
                
                # 3. Склеиваем
                final_df = pd.concat([old_df, new_df], ignore_index=True)
                
                # 4. ВНИМАНИЕ: Для записи в публичную таблицу без API-ключей 
                # мы используем упрощенный коннектор streamlit-gsheets, но с принудительной очисткой
                from streamlit_gsheets import GSheetsConnection
                conn = st.connection("gsheets", type=GSheetsConnection)
                conn.update(spreadsheet=f"https://docs.google.com/spreadsheets/d/{SHEET_ID}", data=final_df)
                
                status.update(label="✅ Данные в таблице!", state="complete")
                st.balloons()
            except Exception as e:
                st.error(f"Критический сбой: {e}")
                st.info("Проверьте, что в таблице нет объединенных ячеек и пустых заголовков.")

# Просмотр
if st.checkbox("Показать архив"):
    st.dataframe(get_data(), width="stretch")
