import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП v40.2 Cloud", layout="wide")

# 2. CSS для красоты и компактности
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; max-width: 98% !important; }
        h1 { font-size: 1.8rem !important; color: #1e3a8a; border-bottom: 2px solid #1e3a8a; }
        .stTabs [data-baseweb="tab"] { height: 45px !important; font-weight: bold; }
        div.stButton > button { background-color: #10b981 !important; color: white !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚂 ОБЛАЧНЫЙ УЧЕТ ПАРАМЕТРОВ КП")

# 3. Подключение к Google Таблицам
# Ссылку на таблицу нужно будет указать в секретах Streamlit Cloud или прямо здесь для теста
url = "https://docs.google.com/spreadsheets/d/1HYkcxtOiEhV7-jOi6TGDxT-exQv78guO9g7b4JVBxAc/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

tab_input, tab_archive = st.tabs(["📥 ВВОД ДАННЫХ", "🗄️ АРХИВ (GOOGLE TABLES)"])

# --- ВКЛАДКА: ВВОД ДАННЫХ ---
with tab_input:
    c1, c2, _ = st.columns([2, 2, 6])
    loco = c1.text_input("📝 № Локомотива", key="loco_nr")
    date_m = c2.date_input("📅 Дата", datetime.now())

    axes_count = 12 if len(loco) == 2 else 6

    cols_name = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
    df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols_name)

    edited_df = st.data_editor(
        df_template, 
        use_container_width=True, 
        key=f"ed_{axes_count}_{loco}",
        height=400 if axes_count == 12 else 280,
        column_config={c: st.column_config.NumberColumn(format="%.1f") for c in cols_name}
    )

    if st.button("📥 ОТПРАВИТЬ В GOOGLE ТАБЛИЦУ", use_container_width=True):
        if not loco:
            st.error("❗ Укажите номер локомотива")
        else:
            try:
                # Читаем текущие данные из таблицы
                existing_data = conn.read(spreadsheet=url)
                
                # Подготавливаем новые строки
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
                
                # Объединяем и обновляем таблицу
                updated_df = pd.concat([existing_data, new_df], ignore_index=True)
                conn.update(spreadsheet=url, data=updated_df)
                
                st.success(f"✅ Данные по {loco} успешно добавлены в Google Таблицу!")
                st.balloons()
            except Exception as e:
                st.error(f"Ошибка подключения к Google: {e}")

# --- ВКЛАДКА: АРХИВ ---
with tab_archive:
    st.subheader("📊 Данные напрямую из Google Drive")
    if st.button("🔄 Обновить данные"):
        df_cloud = conn.read(spreadsheet=url)
        st.dataframe(df_cloud, use_container_width=True, height=600)
    else:
        st.info("Нажмите кнопку выше, чтобы загрузить архив.")
