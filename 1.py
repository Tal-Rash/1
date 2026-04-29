import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import os
import sys
from datetime import datetime, timedelta

try:
    from tkcalendar import DateEntry
except ImportError:
    print("Библиотека tkcalendar не найдена. Установите её: pip install tkcalendar")

class WheelTableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет КП (Версия 40.2: Стабильная)")
        self.root.geometry("1550x900")
        
        self.init_db()
        
        # Настройки допусков
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

    def _bind_mousewheel(self, widget, canvas):
        widget.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def check_value_color(self, param_type, value_str, entry_widget):
        if not value_str:
            entry_widget.config(bg="white")
            return
        try:
            val = float(value_str.replace(',', '.'))
            lim = self.limits[param_type]
            if lim["mode"] == "min":
                if val <= lim["red"]: color = "#ff6666"
                elif val <= lim["yellow"]: color = "#ffff99"
                else: color = "white"
            else:
                if val >= lim["red"]: color = "#ff6666"
                elif val >= lim["yellow"]: color = "#ffff99"
                else: color = "white"
            entry_widget.config(bg=color)
        except ValueError:
            entry_widget.config(bg="white")

    # --- ВВОД ДАННЫХ ---
    def create_input_widgets(self):
        top = ttk.Frame(self.tab_input, padding=15); top.pack(fill="x")
        tk.Label(top, text="Локомотив:", font=('Arial', 12, 'bold')).pack(side="left")
        self.loco_input_box = ttk.Combobox(top, width=15, font=('Arial', 12)); self.loco_input_box.pack(side="left", padx=10)
        self.loco_input_box.bind("<KeyRelease>", self.check_loco_number)
        self.meas_date_entry = DateEntry(top, width=12, font=('Arial', 12), date_pattern='dd.mm.yyyy'); self.meas_date_entry.pack(side="left", padx=20)
        
        self.table_container = tk.Frame(self.tab_input, bg="#d0d0d0")
        self.table_container.pack(pady=15)
        self.draw_input_headers()
        self.set_axes_count(6)
        
        tk.Button(self.tab_input, text="СОХРАНИТЬ", command=self.save_to_db, bg="#4CAF50", fg="white", font=('Arial', 12, 'bold'), padx=40, pady=10).pack(pady=10)

    def draw_input_headers(self):
        headers = ["№ оси", "Гр.Л", "Гр.П", "Пр.Л", "Пр.П", "qR Л", "qR П", "Банд.Л", "Банд.П"]
        for col, text in enumerate(headers):
            tk.Label(self.table_container, text=text, font=('Arial', 10, 'bold'), bg="#f0f0f0", width=14, relief="flat").grid(row=0, column=col, padx=1, pady=1, sticky="nsew")

    def check_loco_number(self, event=None):
        val = self.loco_input_box.get().strip()
        if val.isdigit():
            if len(val) == 2: self.set_axes_count(12)
            elif len(val) in (3, 4): self.set_axes_count(6)

    def set_axes_count(self, count):
        while len(self.all_axes_rows) < count: self.add_axis_row()
        while len(self.all_axes_rows) > count: self.remove_last_axis()

    def add_axis_row(self):
        row_idx = len(self.all_axes_rows) + 1
        lbl = tk.Label(self.table_container, text=f"Ось {row_idx}", font=('Arial', 11, 'bold'), bg="white", width=14, height=2, relief="flat")
        lbl.grid(row=row_idx, column=0, padx=1, pady=1, sticky="nsew")
        current_row_entries = []
        p_types = ["Гребень", "Гребень", "Прокат", "Прокат", "qR", "qR", "Бандаж", "Бандаж"]
        for c in range(8):
            e = tk.Entry(self.table_container, width=14, justify="center", font=('Arial', 12), relief="flat", highlightthickness=0)
            e.grid(row=row_idx, column=c+1, padx=1, pady=1, sticky="nsew", ipady=8)
            e.bind("<KeyRelease>", lambda ev, pt=p_types[c], w=e: self.check_value_color(pt, w.get(), w))
            e.bind("<Key>", lambda ev, r=len(self.all_axes_rows), col=c: self.move_focus(ev, r, col))
            current_row_entries.append(e)
        self.all_axes_rows.append({"label": lbl, "entries": current_row_entries})

    def move_focus(self, event, r, c):
        if event.keysym == 'Up' and r > 0: self.all_axes_rows[r-1]["entries"][c].focus_set()
        elif event.keysym == 'Down' and r < len(self.all_axes_rows) - 1: self.all_axes_rows[r+1]["entries"][c].focus_set()

    def remove_last_axis(self):
        if self.all_axes_rows:
            row = self.all_axes_rows.pop()
            row["label"].destroy()
            for e in row["entries"]: e.destroy()

    def save_to_db(self):
        loco, date = self.loco_input_box.get().strip(), self.meas_date_entry.get().strip()
        if not loco: return
        try:
            for idx, row in enumerate(self.all_axes_rows, start=1):
                v = [float(e.get().replace(',', '.')) if e.get() else 0.0 for e in row["entries"]]
                self.cursor.execute("INSERT INTO measurements (loco_name, wheel_num, f_l, f_r, w_l, w_r, q_l, q_r, t_l, t_r, date) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (loco, idx, *v, date))
            self.conn.commit()
            self.load_archive()
            messagebox.showinfo("!", "Данные сохранены")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    # --- АРХИВ ---
    def create_archive_widgets(self):
        f = ttk.Frame(self.tab_archive, padding=10); f.pack(fill="x")
        self.archive_filter_box = ttk.Combobox(f, state="readonly", width=15); self.archive_filter_box.pack(side="left")
        self.archive_filter_box.bind("<<ComboboxSelected>>", lambda e: self.load_archive())
        ttk.Button(f, text="ВСЕ", command=self.show_all_archive).pack(side="left", padx=5)
        
        self.archive_area = ttk.Frame(self.tab_archive); self.archive_area.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.archive_area, bg="white", highlightthickness=0)
        self.v_scroll = ttk.Scrollbar(self.archive_area, orient="vertical", command=self.canvas.yview)
        self.table_inner = tk.Frame(self.canvas, bg="#d0d0d0") 
        self.table_inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._bind_mousewheel(self.canvas, self.canvas)
        self._bind_mousewheel(self.table_inner, self.canvas)
        self.canvas.create_window((0, 0), window=self.table_inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True); self.v_scroll.pack(side="right", fill="y")
        self.load_archive()

    def draw_archive_header_row(self, row_idx):
        headers = ["Дата", "Локо", "Ось", "Гр.Л", "Гр.П", "Пр.Л", "Пр.П", "qR.Л", "qR.П", "Банд.Л", "Банд.П", "X"]
        for col, text in enumerate(headers):
            h_lbl = tk.Label(self.table_inner, text=text, font=('Arial', 9, 'bold'), bg="#f0f0f0", width=12, relief="flat")
            h_lbl.grid(row=row_idx, column=col, padx=1, pady=1, sticky="nsew")
            self._bind_mousewheel(h_lbl, self.canvas)

    def load_archive(self):
        for w in self.table_inner.winfo_children(): w.destroy()
        loco = self.archive_filter_box.get()
        if loco: self.cursor.execute("SELECT * FROM measurements WHERE loco_name=? ORDER BY date DESC, wheel_num ASC", (loco,))
        else: self.cursor.execute("SELECT * FROM measurements ORDER BY date DESC, loco_name ASC, wheel_num ASC")
        
        rows = self.cursor.fetchall()
        prev_d, prev_l, cur_row = None, None, 0
        for r in rows:
            if prev_d is None or (r[11] != prev_d or r[1] != prev_l):
                self.draw_archive_header_row(cur_row)
                cur_row += 1
            idx_list = [11, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            for i, db_idx in enumerate(idx_list):
                lbl = tk.Label(self.table_inner, text=r[db_idx], bg="white", width=12, relief="flat", font=('Arial', 10))
                lbl.grid(row=cur_row, column=i, padx=1, pady=1, sticky="nsew")
                self._bind_mousewheel(lbl, self.canvas)
            btn = tk.Button(self.table_inner, text="X", command=lambda rid=r[0]: self.delete_row(rid), bg="#ffcdd2", font=('Arial', 8), relief="flat")
            btn.grid(row=cur_row, column=11, padx=1, pady=1, sticky="nsew")
            self._bind_mousewheel(btn, self.canvas)
            prev_d, prev_l, cur_row = r[11], r[1], cur_row + 1
        self.update_loco_lists()

    def delete_row(self, row_id):
        if messagebox.askyesno("?", "Удалить запись?"):
            self.cursor.execute("DELETE FROM measurements WHERE id=?", (row_id,))
            self.conn.commit()
            self.load_archive()

    # --- АНАЛИЗ ---
    def create_history_widgets(self):
        f = ttk.Frame(self.tab_history, padding=10); f.pack(fill="x")
        self.hist_box = ttk.Combobox(f, state="readonly", width=12); self.hist_box.pack(side="left", padx=5)
        self.date_start = DateEntry(f, width=10, date_pattern='dd.mm.yyyy'); self.date_start.pack(side="left")
        self.date_end = DateEntry(f, width=10, date_pattern='dd.mm.yyyy'); self.date_end.pack(side="left", padx=5)
        ttk.Button(f, text="СРАВНИТЬ", command=self.compare_period).pack(side="left")
        
        self.hist_area = ttk.Frame(self.tab_history); self.hist_area.pack(fill="both", expand=True)
        self.hist_canvas = tk.Canvas(self.hist_area, bg="white", highlightthickness=0)
        self.hist_res_frame = tk.Frame(self.hist_canvas, bg="#d0d0d0")
        self.hist_res_frame.bind("<Configure>", lambda e: self.hist_canvas.configure(scrollregion=self.hist_canvas.bbox("all")))
        self._bind_mousewheel(self.hist_canvas, self.hist_canvas)
        self.hist_canvas.create_window((0, 0), window=self.hist_res_frame, anchor="nw")
        self.hist_canvas.pack(side="left", fill="both", expand=True)
        self.draw_history_headers()

    def draw_history_headers(self):
        for col, text in enumerate(["Ось", "Параметр", "Было", "Стало", "Износ"]):
            tk.Label(self.hist_res_frame, text=text, font=('Arial', 10, 'bold'), bg="#f0f0f0", width=18, relief="flat").grid(row=0, column=col, padx=1, pady=1)

    def compare_period(self):
        loco, d1, d2 = self.hist_box.get(), self.date_start.get(), self.date_end.get()
        if not loco: return
        for w in self.hist_res_frame.winfo_children(): 
            if int(w.grid_info()["row"]) > 0: w.destroy()
        
        self.cursor.execute("SELECT DISTINCT date FROM measurements WHERE loco_name=? ORDER BY date ASC", (loco,))
        dates = [r[0] for r in self.cursor.fetchall()]; fmt = "%d.%m.%Y"
        v_dates = [d for d in dates if datetime.strptime(d1, fmt) <= datetime.strptime(d, fmt) <= datetime.strptime(d2, fmt)]
        if len(v_dates) < 2: return
        
        d_old, d_new = v_dates[0], v_dates[-1]
        self.cursor.execute("SELECT * FROM measurements WHERE loco_name=? AND date=?", (loco, d_old))
        prev = {r[2]: r for r in self.cursor.fetchall()}
        self.cursor.execute("SELECT * FROM measurements WHERE loco_name=? AND date=?", (loco, d_new))
        curr = {r[2]: r for r in self.cursor.fetchall()}
        
        params = [("Гребень Л", 3), ("Гребень П", 4), ("Прокат Л", 5), ("Прокат П", 6), ("qR Л", 7), ("qR П", 8), ("Бандаж Л", 9), ("Бандаж П", 10)]
        cur_row = 1
        for w_num in sorted(curr.keys()):
            for p_name, idx in params:
                v_n = curr[w_num][idx]; v_o = prev[w_num][idx] if w_num in prev else 0.0
                vals = [f"Ось {w_num}" if p_name == "Гребень Л" else "", p_name, v_o, v_n, round(v_n - v_o, 2)]
                for c, v in enumerate(vals):
                    l = tk.Label(self.hist_res_frame, text=v, bg="white", width=18, relief="flat")
                    l.grid(row=cur_row, column=c, padx=1, pady=1); self._bind_mousewheel(l, self.hist_canvas)
                cur_row += 1
            for c in range(5): 
                sep = tk.Label(self.hist_res_frame, text="", bg="#f0f0f0", height=1)
                sep.grid(row=cur_row, column=c, sticky="nsew", padx=1, pady=1); self._bind_mousewheel(sep, self.hist_canvas)
            cur_row += 1

    def update_loco_lists(self):
        self.cursor.execute("SELECT DISTINCT loco_name FROM measurements ORDER BY loco_name ASC")
        names = [r[0] for r in self.cursor.fetchall()]
        self.loco_input_box['values'] = names
        self.hist_box['values'] = names
        self.archive_filter_box['values'] = names

    def show_all_archive(self):
        self.archive_filter_box.set(''); self.load_archive()

if __name__ == "__main__":
    root = tk.Tk(); app = WheelTableApp(root); root.mainloop()