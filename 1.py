import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Учет КП Cloud", layout="wide")

# 1. Подключение (теперь оно берет настройки из Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # Пробуем прочитать первый лист. Если пусто — создаем каркас.
        df = conn.read(ttl=0)
        if df is not None and not df.empty:
            # Чистим от пустых столбцов
            return df.loc[:, ~df.columns.str.contains('^Unnamed')]
        return pd.DataFrame(columns=["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"])
    except:
        return pd.DataFrame(columns=["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"])

st.title("🚂 ОБЛАЧНЫЙ УЧЕТ КП")

# Поля ввода
c1, c2 = st.columns(2)
loco = c1.text_input("📝 № Локомотива")
date_m = c2.date_input("📅 Дата", datetime.now())

axes = 12 if len(loco) == 2 else 6
cols = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
df_edit = st.data_editor(pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes)], columns=cols), width="stretch")

if st.button("📥 СОХРАНИТЬ В ОБЛАКО"):
    if not loco:
        st.error("Введите номер!")
    else:
        with st.status("Связь с Google...") as status:
            try:
                current_df = get_data()
                
                rows = []
                for i, (idx, row) in enumerate(df_edit.iterrows(), start=1):
                    rows.append({
                        "Дата": date_m.strftime("%d.%m.%Y"), "Локо": loco, "Ось": i,
                        "Гр_Л": row[0], "Гр_П": row[1], "Пр_Л": row[2], "Пр_П": row[3],
                        "qR_Л": row[4], "qR_П": row[5], "Банд_Л": row[6], "Банд_П": row[7]
                    })
                
                final_df = pd.concat([current_df, pd.DataFrame(rows)], ignore_index=True)
                final_df = final_df.loc[:, ~final_df.columns.str.contains('^Unnamed')]
                
                # Сохраняем (ссылка уже известна из Secrets)
                conn.update(data=final_df)
                status.update(label="✅ Успешно!", state="complete")
                st.balloons()
            except Exception as e:
                status.update(label="❌ Сбой", state="error")
                st.error(f"Текст ошибки: {e}")
