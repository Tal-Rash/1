import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import os
from datetime import datetime

# Проверка наличия календаря
try:
    from tkcalendar import DateEntry
except ImportError:
    messagebox.showwarning("Внимание", "Библиотека tkcalendar не найдена. Установите: pip install tkcalendar")

class WheelTableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет КП (Версия 40.2: Финальная)")
        self.root.geometry("1550x900")
        
        self.init_db()
        
        # Настройки допусков (Желтый - внимание, Красный - брак)
        self.limits = {
            "Гребень": {"yellow": 26.0, "red": 25.0, "mode": "min"},
            "Прокат": {"yellow": 5.0, "red": 7.0, "mode": "max"},
            "qR": {"yellow": 7.0, "red": 6.5, "mode": "min"},
            "Бандаж": {"yellow": 45.0, "red": 40.0, "mode": "min"}
        }
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TNotebook.Tab", font=('Arial', 11, 'bold'), padding=[10, 5])
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        
        # Создание вкладок
        self.tab_input = ttk.Frame(self.notebook)
        self.tab_history = ttk.Frame(self.notebook)
        self.tab_archive = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_input, text=" Ввод данных ")
        self.notebook.add(self.tab_history, text=" Анализ износа ")
        self.notebook.add(self.tab_archive, text=" Архив всех замеров ")
        
        self.all_axes_rows = [] 
        self.create_input_widgets()
        self.create_history_widgets()
        self.create_archive_widgets()

    def init_db(self):
        """Инициализация базы данных на диске D или локально"""
        db_path = r"D:\wheels_data.db"
        try:
            self.conn = sqlite3.connect(db_path)
        except:
            self.conn = sqlite3.connect("wheels_data.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS measurements 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            loco_name TEXT, wheel_num INTEGER, 
                            f_l REAL, f_r REAL, w_l REAL, w_r REAL, 
                            q_l REAL, q_r REAL, t_l REAL, t_r REAL, date TEXT)''')
        self.conn.commit()

    def check_value_color(self, param_type, value_str, entry_widget):
        """Автоматическая подсветка ячеек при вводе"""
        if not value_str:
            entry_widget.config(bg="white")
            return
        try:
            val = float(value_str.replace(',', '.'))
            lim = self.limits[param_type]
            if lim["mode"] == "min":
                if val <= lim["red"]: color = "#ff6666" # Красный
                elif val <= lim["yellow"]: color = "#ffff99" # Желтый
                else: color = "white"
            else:
                if val >= lim["red"]: color = "#ff6666"
                elif val >= lim["yellow"]: color = "#ffff99"
                else: color = "white"
            entry_widget.config(bg=color)
        except ValueError:
            entry_widget.config(bg="white")

    # --- ВКЛАДКА 1: ВВОД ДАННЫХ ---
    def create_input_widgets(self):
        top = ttk.Frame(self.tab_input, padding=15); top.pack(fill="x")
        tk.Label(top, text="Локомотив:", font=('Arial', 12, 'bold')).pack(side="left")
        self.loco_input_box = ttk.Combobox(top, width=15, font=('Arial', 12))
        self.loco_input_box.pack(side="left", padx=10)
        self.loco_input_box.bind("<KeyRelease>", self.check_loco_number)
        
        self.meas_date_entry = DateEntry(top, width=12, font=('Arial', 12), date_pattern='dd.mm.yyyy')
        self.meas_date_entry.pack(side="left", padx=20)
        
        self.table_container = tk.Frame(self.tab_input, bg="#d0d0d0")
        self.table_container.pack(pady=15)
        self.draw_input_headers()
        self.set_axes_count(6)
        
        tk.Button(self.tab_input, text="СОХРАНИТЬ В БАЗУ", command=self.save_to_db, 
                  bg="#4CAF50", fg="white", font=('Arial', 12, 'bold'), padx=40, pady=10).pack(pady=10)

    def draw_input_headers(self):
        headers = ["№ оси", "Гр.Л", "Гр.П", "Пр.Л", "Пр.П", "qR Л", "qR П", "Банд.Л", "Банд.П"]
        for col, text in enumerate(headers):
            tk.Label(self.table_container, text=text, font=('Arial', 10, 'bold'), 
                     bg="#f0f0f0", width=14, relief="flat").grid(row=0, column=col, padx=1, pady=1)

    def check_loco_number(self, event=None):
        val = self.loco_input_box.get().strip()
        if val.isdigit():
            if len(val) == 2: self.set_axes_count(12)
            elif len(val) >= 3: self.set_axes_count(6)

    def set_axes_count(self, count):
        while len(self.all_axes_rows) < count: self.add_axis_row()
        while len(self.all_axes_rows) > count: self.remove_last_axis()

    def add_axis_row(self):
        row_idx = len(self.all_axes_rows) + 1
        lbl = tk.Label(self.table_container, text=f"Ось {row_idx}", font=('Arial', 11, 'bold'), bg="white", width=14, height=2)
        lbl.grid(row=row_idx, column=0, padx=1, pady=1)
        
        current_row_entries = []
        p_types = ["Гребень", "Гребень", "Прокат", "Прокат", "qR", "qR", "Бандаж", "Бандаж"]
        for c in range(8):
            e = tk.Entry(self.table_container, width=14, justify="center", font=('Arial', 12))
            e.grid(row=row_idx, column=c+1, padx=1, pady=1, ipady=8)
            e.bind("<KeyRelease>", lambda ev, pt=p_types[c], w=e: self.check_value_color(pt, w.get(), w))
            current_row_entries.append(e)
        self.all_axes_rows.append({"label": lbl, "entries": current_row_entries})

    def remove_last_axis(self):
        if self.all_axes_rows:
            row = self.all_axes_rows.pop()
            row["label"].destroy()
            for e in row["entries"]: e.destroy()

    def save_to_db(self):
        loco = self.loco_input_box.get().strip()
        date = self.meas_date_entry.get().strip()
        if not loco: 
            messagebox.showwarning("Внимание", "Введите номер локомотива")
            return
        try:
            for idx, row in enumerate(self.all_axes_rows, start=1):
                v = [float(e.get().replace(',', '.')) if e.get() else 0.0 for e in row["entries"]]
                self.cursor.execute("INSERT INTO measurements (loco_name, wheel_num, f_l, f_r, w_l, w_r, q_l, q_r, t_l, t_r, date) VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                                    (loco, idx, *v, date))
            self.conn.commit()
            messagebox.showinfo("Успех", "Данные сохранены")
            self.load_archive()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка БД: {e}")

    # --- ВКЛАДКА 2: АНАЛИЗ ---
    def create_history_widgets(self):
        f = ttk.Frame(self.tab_history, padding=10); f.pack(fill="x")
        self.hist_box = ttk.Combobox(f, width=15); self.hist_box.pack(side="left", padx=5)
        tk.Label(f, text="С:").pack(side="left")
        self.date_start = DateEntry(f, width=10, date_pattern='dd.mm.yyyy'); self.date_start.pack(side="left", padx=5)
        tk.Label(f, text="По:").pack(side="left")
        self.date_end = DateEntry(f, width=10, date_pattern='dd.mm.yyyy'); self.date_end.pack(side="left", padx=5)
        ttk.Button(f, text="СРАВНИТЬ", command=self.compare_period).pack(side="left", padx=10)
        
        self.hist_area = tk.Frame(self.tab_history, bg="white")
        self.hist_area.pack(fill="both", expand=True)
        self.hist_table = tk.Frame(self.hist_area, bg="#d0d0d0")
        self.hist_table.pack(pady=10)

    def compare_period(self):
        # Удаляем старые результаты
        for w in self.hist_table.winfo_children(): w.destroy()
        
        loco = self.hist_box.get()
        if not loco: return
        
        # Логика сравнения первой и последней даты в периоде
        self.cursor.execute("SELECT DISTINCT date FROM measurements WHERE loco_name=? ORDER BY date ASC", (loco,))
        dates = [r[0] for r in self.cursor.fetchall()]
        if len(dates) < 2:
            messagebox.showinfo("Инфо", "Для анализа нужно минимум 2 замера")
            return

        # Шапка таблицы анализа
        cols = ["Ось", "Параметр", "Было", "Стало", "Износ"]
        for i, text in enumerate(cols):
            tk.Label(self.hist_table, text=text, font=('Arial', 10, 'bold'), width=15).grid(row=0, column=i, padx=1, pady=1)

        # Выборка данных
        d_old, d_new = dates[0], dates[-1]
        self.cursor.execute("SELECT * FROM measurements WHERE loco_name=? AND date=?", (loco, d_old))
        prev_data = {r[2]: r for r in self.cursor.fetchall()}
        self.cursor.execute("SELECT * FROM measurements WHERE loco_name=? AND date=?", (loco, d_new))
        curr_data = {r[2]: r for r in self.cursor.fetchall()}

        row_idx = 1
        params = [("Гребень Л", 3), ("Гребень П", 4), ("Прокат Л", 5), ("Прокат П", 6)]
        
        for ax in sorted(curr_data.keys()):
            for p_name, p_idx in params:
                v_old = prev_data[ax][p_idx] if ax in prev_data else 0
                v_curr = curr_data[ax][p_idx]
                diff = round(v_curr - v_old, 2)
                
                tk.Label(self.hist_table, text=f"Ось {ax}", bg="white").grid(row=row_idx, column=0, sticky="nsew")
                tk.Label(self.hist_table, text=p_name, bg="white").grid(row=row_idx, column=1, sticky="nsew")
                tk.Label(self.hist_table, text=v_old, bg="white").grid(row=row_idx, column=2, sticky="nsew")
                tk.Label(self.hist_table, text=v_curr, bg="white").grid(row=row_idx, column=3, sticky="nsew")
                tk.Label(self.hist_table, text=diff, bg="#f0f0f0", fg="red" if diff > 0.5 else "black").grid(row=row_idx, column=4, sticky="nsew")
                row_idx += 1

    # --- ВКЛАДКА 3: АРХИВ ---
    def create_archive_widgets(self):
        f = ttk.Frame(self.tab_archive, padding=10); f.pack(fill="x")
        self.archive_filter = ttk.Combobox(f, width=15); self.archive_filter.pack(side="left")
        ttk.Button(f, text="ФИЛЬТР", command=self.load_archive).pack(side="left", padx=5)
        
        self.tree = ttk.Treeview(self.tab_archive, columns=("1","2","3","4","5","6","7","8"), show='headings')
        cols = [("1","Дата"), ("2","Локо"), ("3","Ось"), ("4","Гр.Л"), ("5","Гр.П"), ("6","Пр.Л"), ("7","Пр.П"), ("8","ID")]
        for c, h in cols:
            self.tree.heading(c, text=h)
            self.tree.column(c, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.load_archive()

    def load_archive(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        loco = self.archive_filter.get()
        if loco:
            self.cursor.execute("SELECT date, loco_name, wheel_num, f_l, f_r, w_l, w_r, id FROM measurements WHERE loco_name=? ORDER BY id DESC", (loco,))
        else:
            self.cursor.execute("SELECT date, loco_name, wheel_num, f_l, f_r, w_l, w_r, id FROM measurements ORDER BY id DESC LIMIT 200")
        
        for r in self.cursor.fetchall():
            self.tree.insert("", "end", values=r)
        self.update_lists()

    def update_lists(self):
        self.cursor.execute("SELECT DISTINCT loco_name FROM measurements")
        names = [r[0] for r in self.cursor.fetchall()]
        self.loco_input_box['values'] = names
        self.hist_box['values'] = names
        self.archive_filter['values'] = names

if __name__ == "__main__":
    root = tk.Tk()
    app = WheelTableApp(root)
    root.mainloop()
