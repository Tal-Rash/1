import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП v40.2 Cloud", layout="wide")

# --- ССЫЛКА НА ТАБЛИЦУ (ЗАМЕНИТЕ НА СВОЮ) ---
# Убедитесь, что доступ: "Все, у кого есть ссылка — Редактор"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1HYkcxtOiEhV7-jOi6TGDxT-exQv78guO9g7b4JVBxAc/edit?usp=sharing"

# 2. Компактный и красивый CSS
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; max-width: 98% !important; }
        h1 { font-size: 1.8rem !important; color: #1e3a8a; border-bottom: 2px solid #1e3a8a; margin-bottom: 0.5rem !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 5px; }
        .stTabs [data-baseweb="tab"] { height: 40px !important; font-weight: bold; font-size: 16px !important; }
        .stTabs [aria-selected="true"] { background-color: #1e3a8a !important; color: white !important; border-radius: 5px; }
        div.stButton > button { background-color: #10b981 !important; color: white !important; font-weight: bold !important; height: 3em !important; }
        [data-testid="stDataEditor"] div { font-size: 0.9rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Подключение к Google Таблицам
conn = st.connection("gsheets", type=GSheetsConnection)

def get_cloud_data():
    try:
        return conn.read(spreadsheet=SPREADSHEET_URL)
    except:
        return pd.DataFrame(columns=["Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"])

st.title("🚂 ОБЛАЧНЫЙ УЧЕТ ПАРАМЕТРОВ КП")

tab_input, tab_archive, tab_analysis = st.tabs(["📥 ВВОД ДАННЫХ", "🗄️ АРХИВ ТАБЛИЦЫ", "📊 АНАЛИЗ"])

# --- ВКЛАДКА: ВВОД ДАННЫХ ---
with tab_input:
    c1, c2, _ = st.columns([2, 2, 6])
    loco = c1.text_input("📝 № Локомотива", placeholder="Введите №", key="loco_input")
    date_m = c2.date_input("📅 Дата замера", datetime.now())

    # УСЛОВИЕ: 2 знака = 12 осей, 3 и более = 6 осей
    axes_count = 12 if len(loco) == 2 else 6

    st.write(f"#### Сетка замера ({axes_count} осей)")
    
    # Структура таблицы ввода
    cols_name = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
    df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols_name)

    # Редактор таблицы (Компактный)
    edited_df = st.data_editor(
        df_template, 
        use_container_width=True, 
        key=f"ed_{axes_count}_{loco}",
        height=420 if axes_count == 12 else 260,
        column_config={c: st.column_config.NumberColumn(format="%.1f") for c in cols_name}
    )

    if st.button("📥 ОТПРАВИТЬ В GOOGLE ТАБЛИЦУ", use_container_width=True):
        if not loco:
            st.error("❗ Ошибка: Укажите номер локомотива")
        else:
            with st.spinner('Сохранение в облако...'):
                try:
                    # Читаем старые данные
                    existing_df = get_cloud_data()
                    
                    # Готовим новые данные
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
                    
                    # Объединяем и отправляем обратно
                    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                    conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
                    
                    st.success(f"✅ Данные по локомотиву {loco} успешно сохранены!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Ошибка доступа к Google: {e}")

# --- ВКЛАДКА: АРХИВ ---
with tab_archive:
    st.subheader("🗄️ Все записи из Google Drive")
    if st.button("🔄 Обновить данные из таблицы"):
        df_archive = get_cloud_data()
        st.dataframe(df_archive, use_container_width=True, height=600)
    else:
        st.info("Нажмите кнопку выше для загрузки архива.")

# --- ВКЛАДКА: АНАЛИЗ ---
with tab_analysis:
    st.subheader("📊 Анализ износа")
    st.write("Раздел будет доступен после накопления данных.")
