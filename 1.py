import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП v40.2 Cloud", layout="wide")

# --- ВСТАВЬТЕ ВАШУ ССЫЛКУ ТУТ ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/ВАШ_ID_ЗДЕСЬ/edit?usp=sharing"

# 2. Подключение
conn = st.connection("gsheets", type=GSheetsConnection)

def get_cloud_data():
    try:
        # ttl=0 гарантирует, что мы всегда видим актуальные данные
        return conn.read(spreadsheet=SPREADSHEET_URL, ttl=0)
    except Exception:
        # Если таблица пустая, создаем каркас
        return pd.DataFrame(columns=["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"])

# 3. CSS (обновленный)
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; max-width: 98% !important; }
        h1 { font-size: 1.8rem !important; color: #1e3a8a; border-bottom: 2px solid #1e3a8a; }
        div.stButton > button { background-color: #10b981 !important; color: white !important; font-weight: bold !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚂 ОБЛАЧНЫЙ УЧЕТ ПАРАМЕТРОВ КП")

tab_input, tab_archive = st.tabs(["📥 ВВОД ДАННЫХ", "🗄️ АРХИВ"])

# --- ВКЛАДКА: ВВОД ДАННЫХ ---
with tab_input:
    c1, c2, _ = st.columns([2, 2, 6])
    loco = c1.text_input("📝 № Локомотива", key="loco_input")
    date_m = c2.date_input("📅 Дата замера", datetime.now())

    axes_count = 12 if len(loco) == 2 else 6
    
    cols_name = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
    df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols_name)

    # Исправлено согласно логам: width='stretch' вместо use_container_width
    edited_df = st.data_editor(
        df_template, 
        width='stretch', 
        key=f"ed_{axes_count}_{loco}",
        height=420 if axes_count == 12 else 260,
        column_config={c: st.column_config.NumberColumn(format="%.1f") for c in cols_name}
    )

    if st.button("📥 ОТПРАВИТЬ В GOOGLE ТАБЛИЦУ"):
        if not loco:
            st.error("❗ Укажите номер локомотива")
        else:
            try:
                existing_df = get_cloud_data()
                
                # Собираем новые данные
                new_data = []
                for i, (idx, row) in enumerate(edited_df.iterrows(), start=1):
                    new_data.append([
                        date_m.strftime("%d.%m.%Y"), loco, i,
                        row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]
                    ])
                
                new_df = pd.DataFrame(new_data, columns=existing_df.columns)
                
                # Объединяем
                updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                
                # ОЧЕНЬ ВАЖНО: сохраняем обратно
                conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
                st.success("✅ Данные успешно улетели в таблицу!")
                st.balloons()
            except Exception as e:
                st.error(f"Ошибка доступа к Google: {e}")

# --- ВКЛАДКА: АРХИВ ---
with tab_archive:
    if st.button("🔄 Обновить архив"):
        df = get_cloud_data()
        st.dataframe(df, width='stretch', height=600)
