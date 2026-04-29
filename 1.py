import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# 1. Настройка страницы
st.set_page_config(page_title="Учет КП v40.2 Cloud", layout="wide")

# --- ВАША ССЫЛКА ИНТЕГРИРОВАНА ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1HYkcxtOiEhV7-jOi6TGDxT-exQv78guO9g7b4JVBxAc/edit?usp=sharing"

# 2. Подключение к Google Таблицам
conn = st.connection("gsheets", type=GSheetsConnection)

def get_cloud_data():
    try:
        # Пробуем прочитать лист "Лист1". Если в таблице лист называется "Sheet1", замените имя ниже.
        return conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Лист1", ttl=0)
    except Exception:
        # Пытаемся прочитать Sheet1, если Лист1 не найден
        try:
            return conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Sheet1", ttl=0)
        except:
            # Если таблица совсем пустая, создаем структуру столбцов
            return pd.DataFrame(columns=[
                "Дата", "Локо", "Ось", "Гр_Л", "Гр_П", "Пр_Л", "Пр_П", "qR_Л", "qR_П", "Банд_Л", "Банд_П"
            ])

# 3. CSS для компактности и стиля
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; max-width: 98% !important; }
        h1 { font-size: 1.8rem !important; color: #1e3a8a; border-bottom: 2px solid #1e3a8a; margin-bottom: 0.5rem !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] { height: 45px !important; font-weight: bold; font-size: 16px !important; }
        div.stButton > button { 
            background-color: #10b981 !important; 
            color: white !important; 
            font-weight: bold !important; 
            height: 3.5em !important; 
            width: 100%;
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

st.title("🚂 ОБЛАЧНЫЙ УЧЕТ ПАРАМЕТРОВ КП")

tab_input, tab_archive = st.tabs(["📥 ВВОД ДАННЫХ", "🗄️ АРХИВ ЗАМЕРОВ"])

# --- ВКЛАДКА: ВВОД ДАННЫХ ---
with tab_input:
    c1, c2, _ = st.columns([2, 2, 6])
    loco = c1.text_input("📝 № Локомотива", placeholder="Введите №", key="loco_input")
    date_m = c2.date_input("📅 Дата замера", datetime.now())

    # Условие: 2 знака = 12 осей, иначе 6 осей
    axes_count = 12 if len(loco) == 2 else 6

    st.write(f"#### Сетка замера для №{loco if loco else '...'} ({axes_count} осей)")
    
    # Шаблон таблицы
    cols_name = ["Гр Л", "Гр П", "Пр Л", "Пр П", "qR Л", "qR П", "Банд Л", "Банд П"]
    df_template = pd.DataFrame(0.0, index=[f"Ось {i+1}" for i in range(axes_count)], columns=cols_name)

    # Редактор таблицы
    edited_df = st.data_editor(
        df_template, 
        width="stretch", 
        key=f"ed_{axes_count}_{loco}",
        height=420 if axes_count == 12 else 260,
        column_config={c: st.column_config.NumberColumn(format="%.1f") for c in cols_name}
    )

    st.markdown("---")

    if st.button("📥 ОТПРАВИТЬ В GOOGLE ТАБЛИЦУ"):
        if not loco:
            st.error("❗ Ошибка: Сначала введите номер локомотива")
        else:
            with st.status("⏳ Соединение с облаком Google...", expanded=True) as status:
                try:
                    # 1. Получаем текущие записи
                    existing_df = get_cloud_data()
                    
                    # 2. Формируем новые строки
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
                    
                    # 3. Объединяем
                    if not existing_df.empty:
                        # Убираем полностью пустые столбцы/строки если они затесались
                        existing_df = existing_df.dropna(how='all', axis=1).dropna(how='all', axis=0)
                        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                    else:
                        updated_df = new_df
                    
                    # 4. Сохраняем обратно
                    conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
                    
                    status.update(label="✅ Данные успешно сохранены!", state="complete", expanded=False)
                    st.balloons()
                    
                except Exception as e:
                    status.update(label="❌ Ошибка сохранения", state="error")
                    st.error(f"Детальная ошибка: {str(e)}")

# --- ВКЛАДКА: АРХИВ ЗАМЕРОВ ---
with tab_archive:
    st.subheader("🗄️ История замеров из Google Drive")
    if st.button("🔄 Обновить данные из таблицы", key="refresh_archive"):
        with st.spinner("Загрузка..."):
            df_archive = get_cloud_data()
            if not df_archive.empty:
                st.dataframe(df_archive, width="stretch", height=600)
            else:
                st.warning("Таблица пока пуста или недоступна.")
