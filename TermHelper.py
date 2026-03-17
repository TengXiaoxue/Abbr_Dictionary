import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
import re
import keyboard
import glob
import json
 
# ================= 1. 环境与路径 =================
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
 
DB_FILE = os.path.join(application_path, 'term_data.db')
 
# ================= 2. 数据库初始化 =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            abbr TEXT NOT NULL,
            full TEXT NOT NULL,
            desc TEXT,
            source_lib TEXT NOT NULL
        )
    ''')
    c.execute('CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_search ON terms(abbr, full)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_lib ON terms(source_lib)')
    json_files = glob.glob(os.path.join(application_path, '*_lib.json'))
    if json_files:
        for jf in json_files:
            lib_name = os.path.basename(jf).replace('_lib.json', '')
            try:
                with open(jf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        c.execute('INSERT INTO terms (abbr, full, desc, source_lib) VALUES (?,?,?,?)', 
                                  (item.get('abbr',''), item.get('full',''), item.get('desc',''), lib_name))
                os.rename(jf, jf + '.imported')
            except Exception:
                pass
    c.execute('SELECT COUNT(*) FROM terms')
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO terms (abbr, full, desc, source_lib) VALUES ('NDF', 'No Database Found', '没找到任何数据库，请创建（此条可删除）', 'default')")
    conn.commit()
    conn.close()
 
def get_available_libs():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT DISTINCT source_lib FROM terms ORDER BY source_lib')
    libs = [row[0] for row in c.fetchall()]
    conn.close()
    return libs if libs else ['default']
 
def update_ui_state():
    libs = get_available_libs()
    lib_label_var.set(f"📚 数据库模式运转中 | 当前包含模块 ({len(libs)}个): {', '.join(libs)}")
    current_selection = filter_var.get()
    new_options = ["全部模块"] + libs
    filter_combo['values'] = new_options
    if current_selection in new_options:
        filter_combo.set(current_selection)
    else:
        filter_combo.set("全部模块")
 
def save_col_widths():
    try:
        widths = {'abbr': tree.column('abbr', 'width'), 'full': tree.column('full', 'width'), 'desc': tree.column('desc', 'width'), 'source': tree.column('source', 'width')}
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', ('col_widths', json.dumps(widths)))
        conn.commit()
        conn.close()
    except Exception:
        pass
 
def load_col_widths():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT value FROM config WHERE key="col_widths"')
        row = c.fetchone()
        conn.close()
        if row:
            widths = json.loads(row[0])
            for col, w in widths.items():
                tree.column(col, width=w)
    except Exception:
        pass
 
# ================= 3. 极速带筛选搜索 =================

def search(*args):
    query = search_var.get().strip().lower()
    selected_lib = filter_var.get()

    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    sql = 'SELECT id, abbr, full, desc, source_lib FROM terms WHERE 1=1'
    params = []

    if query:
        # 严格的前缀匹配
        search_pattern = f'{query}%'
        # 只匹配缩略词 (abbr) 的开头，
        sql += ' AND abbr LIKE ?'
        params.append(search_pattern)

    if selected_lib and selected_lib != "全部模块":
        sql += ' AND source_lib = ?'
        params.append(selected_lib)

    # 按字母顺序排列显示
    sql += ' ORDER BY abbr ASC LIMIT 1000' 
    c.execute(sql, tuple(params))
    rows = c.fetchall()
    conn.close()
    for r in rows:
        tree.insert('', 'end', values=r)
 
 
# ================= 4. 增删改查逻辑 =================
def manual_add():
    add_win = tk.Toplevel(root)
    add_win.title("➕ 手动添加词条")
    add_win.geometry("380x350")
    add_win.attributes('-topmost', True)
    tk.Label(add_win, text="缩略词:", font=('微软雅黑', 10)).pack(pady=(15, 5))
    abbr_var = tk.StringVar()
    tk.Entry(add_win, textvariable=abbr_var, font=('微软雅黑', 10), width=30).pack()
    tk.Label(add_win, text="全称:", font=('微软雅黑', 10)).pack(pady=(10, 5))
    full_var = tk.StringVar()
    tk.Entry(add_win, textvariable=full_var, font=('微软雅黑', 10), width=30).pack()
    tk.Label(add_win, text="中文解释:", font=('微软雅黑', 10)).pack(pady=(10, 5))
    desc_var = tk.StringVar()
    tk.Entry(add_win, textvariable=desc_var, font=('微软雅黑', 10), width=30).pack()
    libs = get_available_libs()
    tk.Label(add_win, text="保存到哪个模块?", font=('微软雅黑', 10, 'bold'), fg="#008CBA").pack(pady=(15, 5))
    lib_combo = ttk.Combobox(add_win, values=libs, font=('微软雅黑', 10), width=28)
    if libs: lib_combo.current(0)
    lib_combo.pack()
 
    def save_new_entry():
        abbr, full, desc, target_lib = abbr_var.get().strip(), full_var.get().strip(), desc_var.get().strip(), lib_combo.get().strip() or "default"
        if not abbr: return
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO terms (abbr, full, desc, source_lib) VALUES (?,?,?,?)', (abbr, full, desc, target_lib))
        conn.commit()
        conn.close()
        update_ui_state()
        search()
        add_win.destroy()
 
    tk.Button(add_win, text="💾 保存词条", bg="#4CAF50", fg="white", font=('微软雅黑', 10, 'bold'), command=save_new_entry).pack(pady=20)
 
def edit_selected(event=None):
    selected_items = tree.selection()
    if not selected_items or len(selected_items) > 1: return
    item_id, orig_abbr, orig_full, orig_desc, orig_lib = tree.item(selected_items[0], 'values')
 
    edit_win = tk.Toplevel(root)
    edit_win.title("✏️ 编辑词条")
    edit_win.geometry("380x350")
    edit_win.attributes('-topmost', True)
    tk.Label(edit_win, text="缩略词:", font=('微软雅黑', 10)).pack(pady=(15, 5))
    abbr_var = tk.StringVar(value=orig_abbr)
    tk.Entry(edit_win, textvariable=abbr_var, font=('微软雅黑', 10), width=30).pack()
    tk.Label(edit_win, text="全称:", font=('微软雅黑', 10)).pack(pady=(10, 5))
    full_var = tk.StringVar(value=orig_full)
    tk.Entry(edit_win, textvariable=full_var, font=('微软雅黑', 10), width=30).pack()
    tk.Label(edit_win, text="中文解释:", font=('微软雅黑', 10)).pack(pady=(10, 5))
    desc_var = tk.StringVar(value=orig_desc)
    tk.Entry(edit_win, textvariable=desc_var, font=('微软雅黑', 10), width=30).pack()
    tk.Label(edit_win, text="所属模块 (修改将转移词条):", font=('微软雅黑', 10)).pack(pady=(10, 5))
    libs = get_available_libs()
    lib_edit_combo = ttk.Combobox(edit_win, values=libs, font=('微软雅黑', 10), width=28)
    lib_edit_combo.set(orig_lib)
    lib_edit_combo.pack()
 
    def save_changes():
        new_abbr, new_full, new_desc, new_lib = abbr_var.get().strip(), full_var.get().strip(), desc_var.get().strip(), lib_edit_combo.get().strip() or "default"
        if not new_abbr: return
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('UPDATE terms SET abbr=?, full=?, desc=?, source_lib=? WHERE id=?', (new_abbr, new_full, new_desc, new_lib, item_id))
        conn.commit()
        conn.close()
        update_ui_state()
        search()
        edit_win.destroy()
 
    tk.Button(edit_win, text="💾 保存修改", bg="#FF9800", fg="white", font=('微软雅黑', 10, 'bold'), command=save_changes).pack(pady=15)
 
def delete_selected():
    selected_items = tree.selection()
    if not selected_items: return
    if messagebox.askyesno("确认删除", f"确定要彻底删除选中的 {len(selected_items)} 个词条吗？"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        for item in selected_items:
            c.execute('DELETE FROM terms WHERE id=?', (tree.item(item, 'values')[0],))
        conn.commit()
        conn.close()
        update_ui_state()
        search()
 
def extract_from_clipboard():
    try: clipboard_text = root.clipboard_get()
    except tk.TclError: return
    found_abbrs = {word for word in set(re.findall(r'\b[A-Z0-9]{2,10}\b', clipboard_text)) if not word.isdigit()}
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT abbr FROM terms')
    new_abbrs = list(found_abbrs - {row[0].upper() for row in c.fetchall()})
    conn.close()
    if not new_abbrs: return messagebox.showinfo("提示", "剪贴板里没有发现全新的缩略词！")
    show_batch_add_window(new_abbrs)
 
def show_batch_add_window(new_abbrs):
    add_win = tk.Toplevel(root)
    add_win.title("✨ 发现新缩略词！请完善信息")
    add_win.geometry("550x450")
    add_win.attributes('-topmost', True)
    tk.Label(add_win, text=f"从剪贴板识别到 {len(new_abbrs)} 个新词，请补全（留空则不保存）：", font=('微软雅黑', 10), fg="gray").pack(pady=5)
    entries = []
    for abbr in new_abbrs[:6]: 
        frame = tk.Frame(add_win)
        frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frame, text=abbr, font=('微软雅黑', 11, 'bold'), width=8, anchor='w').pack(side=tk.LEFT)
        full_var, desc_var = tk.StringVar(), tk.StringVar()
        tk.Entry(frame, textvariable=full_var, width=22).pack(side=tk.LEFT, padx=5)
        full_var.set("在此输入全称...")
        tk.Entry(frame, textvariable=desc_var, width=22).pack(side=tk.LEFT, padx=5)
        desc_var.set("在此输入中文...")
        entries.append((abbr, full_var, desc_var))
 
    bot_frame = tk.Frame(add_win)
    bot_frame.pack(pady=20)
    tk.Label(bot_frame, text="保存至模块:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=5)
    libs = get_available_libs()
    lib_combo = ttk.Combobox(bot_frame, values=libs, width=15)
    if libs: lib_combo.current(0)
    lib_combo.pack(side=tk.LEFT, padx=5)
 
    def save_new_words():
        target_lib = lib_combo.get().strip() or "default"
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        for abbr, f_var, d_var in entries:
            full, desc = f_var.get().strip(), d_var.get().strip()
            if full and "在此输入" not in full and desc and "在此输入" not in desc:
                c.execute('INSERT INTO terms (abbr, full, desc, source_lib) VALUES (?,?,?,?)', (abbr, full, desc, target_lib))
        conn.commit()
        conn.close()
        update_ui_state()
        search()
        add_win.destroy()
    tk.Button(bot_frame, text="💾 保存提取", bg="#4CAF50", fg="white", font=('微软雅黑', 10, 'bold'), command=save_new_words).pack(side=tk.LEFT, padx=15)
 
# ================= 5. 卡片式鼠标悬停功能 =================
tooltip_win = None
tooltip_id = None
last_hovered_item = None
mouse_x = 0
mouse_y = 0
 
def on_tree_motion(event):
    global tooltip_id, last_hovered_item, mouse_x, mouse_y
    mouse_x, mouse_y = event.x_root, event.y_root
    # 只要鼠标在某一行上，无论在哪一列都触发
    item = tree.identify_row(event.y)
    if not item:
        hide_tooltip()
        last_hovered_item = None
        return
    if item == last_hovered_item:
        return # 还在同一行，不重复触发
    last_hovered_item = item
    hide_tooltip() # 换行了，先隐藏之前的提示框
    # 延迟 0.5 秒弹出
    tooltip_id = tree.after(500, lambda: show_tooltip(item))
 
def show_tooltip(item):
    global tooltip_win
    values = tree.item(item, 'values')
    if not values: return
    abbr_text = str(values[1]).strip()
    full_text = str(values[2]).strip()
    desc_text = str(values[3]).strip()
    display_text = f"📌 {abbr_text}\n"
    if full_text: display_text += f"全称：{full_text}\n"
    if desc_text: display_text += f"解释：{desc_text}"
    display_text = display_text.strip()
    if not display_text: return
    tooltip_win = tk.Toplevel(root)
    tooltip_win.wm_overrideredirect(True) 
    # 【修复核心点】必须加上这行代码，让悬浮框突破主窗口的置顶限制！
    tooltip_win.attributes('-topmost', True) 
    tooltip_win.wm_geometry(f"+{mouse_x + 15}+{mouse_y + 15}")
    label = tk.Label(tooltip_win, text=display_text, justify=tk.LEFT,
                     background="#FFFFE1", foreground="#333333",
                     relief=tk.SOLID, borderwidth=1,
                     font=('微软雅黑', 10), wraplength=450)
    label.pack(ipadx=10, ipady=8)
 
def hide_tooltip(event=None):
    global tooltip_win, tooltip_id, last_hovered_item
    if tooltip_id:
        tree.after_cancel(tooltip_id)
        tooltip_id = None
    if tooltip_win:
        tooltip_win.destroy()
        tooltip_win = None
    if event: 
        last_hovered_item = None
 
# ================= 6. 窗口控制与主程序 =================
def hide_window(event=None):
    save_col_widths()
    hide_tooltip() 
    root.withdraw()
 
def on_closing():
    save_col_widths()
    root.destroy()
    os._exit(0)
 
def show_window():
    root.after(0, _bring_to_front)
 
def _bring_to_front():
    update_ui_state()
    search()
    root.deiconify()
    root.attributes('-topmost', True)
    root.focus_force()
    search_entry.focus()
    search_entry.select_range(0, tk.END)
 
keyboard.unhook_all()
init_db()
 
root = tk.Tk()
root.title("📚 极速数据库词典 (Alt+Q 唤醒)")
root.geometry("950x550")
root.protocol("WM_DELETE_WINDOW", on_closing)
 
lib_label_var = tk.StringVar()
tk.Label(root, textvariable=lib_label_var, font=('微软雅黑', 9), fg="#e67e22").pack(pady=(10, 0))
 
top_frame = tk.Frame(root)
top_frame.pack(pady=10, fill=tk.X, padx=20)
 
search_inner_frame = tk.Frame(top_frame)
search_inner_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
 
filter_var = tk.StringVar()
filter_combo = ttk.Combobox(search_inner_frame, textvariable=filter_var, state="readonly", width=12, font=('微软雅黑', 11))
filter_combo.pack(side=tk.LEFT, padx=(0, 10))
filter_combo.bind('<<ComboboxSelected>>', search)
 
tk.Label(search_inner_frame, text="🔍", font=('微软雅黑', 14)).pack(side=tk.LEFT)
search_var = tk.StringVar()
search_var.trace_add('write', search) 
search_entry = tk.Entry(search_inner_frame, textvariable=search_var, font=('微软雅黑', 14))
search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
 
btn_frame = tk.Frame(top_frame)
btn_frame.pack(side=tk.RIGHT)
 
tk.Button(btn_frame, text="➕ 手动添加", bg="#4CAF50", fg="white", font=('微软雅黑', 9, 'bold'), command=manual_add).pack(side=tk.LEFT, padx=3)
tk.Button(btn_frame, text="✏️ 编辑选中", bg="#FF9800", fg="white", font=('微软雅黑', 9, 'bold'), command=edit_selected).pack(side=tk.LEFT, padx=3)
tk.Button(btn_frame, text="🗑️ 删除选中", bg="#f44336", fg="white", font=('微软雅黑', 9, 'bold'), command=delete_selected).pack(side=tk.LEFT, padx=3)
tk.Button(btn_frame, text="📋 剪贴板提取", bg="#008CBA", fg="white", font=('微软雅黑', 9, 'bold'), command=extract_from_clipboard).pack(side=tk.LEFT, padx=3)
 
# ================= 表格 UI 与 滚动条 =================
tree_frame = tk.Frame(root)
tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
 
v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
 
columns = ('id', 'abbr', 'full', 'desc', 'source')
tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode="extended", 
                    displaycolumns=('abbr', 'full', 'desc', 'source'),
                    yscrollcommand=v_scroll.set, 
                    xscrollcommand=h_scroll.set)
 
v_scroll.config(command=tree.yview)
h_scroll.config(command=tree.xview)
 
v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
 
tree.heading('abbr', text='缩略词')
tree.heading('full', text='全称')
tree.heading('desc', text='中文解释')
tree.heading('source', text='所属模块')
 
tree.column('abbr', width=120, minwidth=80, anchor=tk.CENTER, stretch=False)
tree.column('full', width=300, minwidth=150, anchor=tk.W, stretch=False)
tree.column('source', width=100, minwidth=80, anchor=tk.CENTER, stretch=False)
tree.column('desc', width=450, minwidth=200, anchor=tk.W, stretch=True)
 
load_col_widths()
tree.bind('<Double-1>', edit_selected)
 
# 绑定鼠标移动事件以触发提示框，离开表格或点击时销毁
tree.bind('<Motion>', on_tree_motion)
tree.bind('<Leave>', hide_tooltip)
tree.bind('<Button-1>', hide_tooltip)
 
style = ttk.Style()
style.configure("Treeview", font=('微软雅黑', 10), rowheight=25)
style.configure("Treeview.Heading", font=('微软雅黑', 11, 'bold'))
 
root.bind('<Escape>', hide_window)
keyboard.add_hotkey('alt+q', show_window)
 
update_ui_state()
_bring_to_front()
root.mainloop()