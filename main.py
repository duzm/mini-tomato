"""
@Author: duzm
@Time: 2025年2月22日
@Description: 番茄钟。特点：悬浮半透明小窗口倒计时。
"""

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox

import pystray
from PIL import Image

if sys.platform == "win32":
    from pystray import _win32 as pystray_win32

from constant import APP_NAME, AUTHOR, DEFAULT_BREAK_TIME, DEFAULT_WORK_TIME, GITHUB_URL, ICON_FILE, VERSION

# 全局变量，用于跟踪当前的悬浮窗口
float_window = None
root = None
entry = None
tray_icon = None
tray_thread = None
tray_visible = False
action_queue = queue.SimpleQueue()


if sys.platform == "win32":
    class TrayIcon(pystray.Icon):
        def _on_notify(self, wparam, lparam):
            if lparam == pystray_win32.win32.WM_LBUTTONUP:
                self()
            elif self._menu_handle and lparam == pystray_win32.win32.WM_RBUTTONUP:
                pystray_win32.win32.SetForegroundWindow(self._hwnd)

                point = pystray_win32.wintypes.POINT()
                pystray_win32.win32.GetCursorPos(pystray_win32.ctypes.byref(point))

                hmenu, descriptors = self._menu_handle
                index = pystray_win32.win32.TrackPopupMenuEx(
                    hmenu,
                    pystray_win32.win32.TPM_LEFTALIGN | pystray_win32.win32.TPM_BOTTOMALIGN
                    | pystray_win32.win32.TPM_RETURNCMD,
                    point.x,
                    point.y,
                    self._menu_hwnd,
                    None,
                )
                if index > 0:
                    descriptors[index - 1](self)
else:
    TrayIcon = pystray.Icon


def resource_path(relative_path):
    """获取资源绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def show_about():
    """显示关于对话框"""
    about_window = tk.Toplevel(root)
    about_window.withdraw()  # 先隐藏窗口，避免窗口闪烁
    about_window.title("关于")
    about_window.configure(bg='#C7EDCC')
    about_window.iconbitmap(resource_path(ICON_FILE))

    # 增加窗口高度以容纳所有文本
    window_width = 300
    window_height = 240
    x_position = root.winfo_x() + (root.winfo_width() - window_width) // 2
    y_position = root.winfo_y() + (root.winfo_height() - window_height) // 2
    about_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # 禁止调整窗口大小
    about_window.resizable(False, False)

    # 创建文本标签
    about_text = f"""
{APP_NAME} {VERSION}

一个简单而实用的番茄工作法计时器。
特点：悬浮半透明小窗口。

作者: {AUTHOR}
GitHub: {GITHUB_URL}
"""
    label = tk.Label(about_window, text=about_text, bg='#C7EDCC', fg='#333333', justify=tk.LEFT, padx=20, pady=0)
    label.pack()

    # 确定按钮
    ok_button = tk.Button(
        about_window, text="确定", command=about_window.destroy, bg='#A3DCB1', fg='#333333', width=10, height=1
    )
    ok_button.pack(pady=10)

    # 设置模态窗口
    about_window.transient(root)
    about_window.grab_set()
    about_window.deiconify()
    root.wait_window(about_window)


def get_focus_minutes():
    value = entry.get().strip()
    if not value:
        return DEFAULT_WORK_TIME // 60
    try:
        minutes = int(value)
    except ValueError:
        return DEFAULT_WORK_TIME // 60
    return minutes if minutes > 0 else DEFAULT_WORK_TIME // 60


def start_focus_session():
    start_timer(work_time=get_focus_minutes() * 60)


def start_break_session():
    start_timer(work_time=get_focus_minutes() * 60, break_time=DEFAULT_BREAK_TIME, is_work_time=False)


def start_timer(work_time=DEFAULT_WORK_TIME, break_time=DEFAULT_BREAK_TIME, is_work_time=True):
    global float_window

    # 如果已经存在一个悬浮窗口，先销毁它
    if float_window is not None:
        float_window.destroy()

    # 创建新的悬浮窗口
    float_window = tk.Toplevel(root)
    float_window.overrideredirect(True)  # 去掉窗口边框
    float_window.attributes("-topmost", True)  # 窗口置顶
    float_window.attributes("-alpha", 0.5)  # 设置窗口透明度

    # 获取屏幕宽度和高度
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 设置悬浮窗口的初始位置为屏幕的偏右下方
    window_width = 200
    window_height = 100
    x_position = screen_width - window_width - 50
    y_position = screen_height - window_height - 70
    float_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    label = tk.Label(float_window, text="", font=("Helvetica", 48))
    label.pack(expand=True)

    # 实现窗口拖动功能
    def start_move(event):
        float_window.x = event.x
        float_window.y = event.y

    def do_move(event):
        x = event.x - float_window.x + float_window.winfo_x()
        y = event.y - float_window.y + float_window.winfo_y()
        float_window.geometry(f"+{x}+{y}")

    float_window.bind("<Button-1>", start_move)
    float_window.bind("<B1-Motion>", do_move)

    # 倒计时功能
    def countdown(count):
        mins, secs = divmod(count, 60)
        time_format = '{:02d}:{:02d}'.format(mins, secs)
        label.config(text=time_format)
        if count > 0:
            float_window.after(1000, countdown, count - 1)
        else:
            float_window.destroy()
            if is_work_time:
                messagebox.showinfo("时间到", "工作时间结束！休息一下吧~")
                start_timer(work_time=work_time, break_time=break_time, is_work_time=False)  # 开始休息时间
            else:
                messagebox.showinfo("时间到", "休息时间结束！开始新的工作周期")
                start_timer(work_time=work_time, break_time=break_time, is_work_time=True)  # 开始工作时间

    countdown(work_time if is_work_time else break_time)


def enqueue_tray_action(action):
    def callback(icon, item):
        action_queue.put(action)

    return callback


def is_root_visible():
    return root is not None and root.winfo_exists() and root.state() != "withdrawn"


def get_window_toggle_text(item=None):
    return "最小化窗口" if is_root_visible() else "显示窗口"


def refresh_tray_menu():
    if tray_icon is not None:
        tray_icon.update_menu()


def create_tray_image():
    return Image.open(resource_path(ICON_FILE))


def create_tray_menu():
    return pystray.Menu(
        pystray.MenuItem(get_window_toggle_text, enqueue_tray_action("toggle_window"), default=True, visible=False),
        pystray.MenuItem(get_window_toggle_text, enqueue_tray_action("toggle_window")),
        pystray.MenuItem("开始专注", enqueue_tray_action("start_focus")),
        pystray.MenuItem("开始休息", enqueue_tray_action("start_break")),
        pystray.MenuItem("退出", enqueue_tray_action("quit")),
    )


def ensure_tray_icon():
    global tray_icon, tray_thread

    if tray_icon is not None:
        return tray_icon

    tray_icon = TrayIcon(APP_NAME, create_tray_image(), APP_NAME, create_tray_menu())
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()
    return tray_icon


def show_tray_icon():
    global tray_visible

    ensure_tray_icon()
    if tray_icon is not None:
        tray_icon.visible = True
        tray_visible = True
        refresh_tray_menu()


def hide_tray_icon():
    global tray_icon, tray_thread, tray_visible

    if tray_icon is not None:
        tray_icon.stop()
        tray_icon = None
        tray_thread = None
    tray_visible = False


def hide_window_to_tray():
    if root.winfo_exists() and root.state() != "withdrawn":
        root.withdraw()
    show_tray_icon()
    refresh_tray_menu()


def restore_window():
    if not root.winfo_exists():
        return
    show_tray_icon()
    root.deiconify()
    root.state("normal")
    root.lift()
    root.focus_force()
    refresh_tray_menu()


def confirm_close_action():
    dialog = tk.Toplevel(root)
    dialog.withdraw()
    dialog.title("关闭程序")
    dialog.configure(bg='#C7EDCC')
    dialog.resizable(False, False)
    dialog.iconbitmap(resource_path(ICON_FILE))

    result = {"action": None}

    def close_dialog(action=None):
        result["action"] = action
        dialog.destroy()

    def bind_hover_style(button):
        def on_enter(event):
            event.widget.config(bg='#8DCEA0', font=("", 11, "bold"))

        def on_leave(event):
            event.widget.config(bg='#A3DCB1', font=("", 11))

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

    dialog.protocol("WM_DELETE_WINDOW", close_dialog)

    width = min(root.winfo_width() - 24, 276)
    height = 142
    x_position = root.winfo_x() + (root.winfo_width() - width) // 2
    y_position = root.winfo_y() + (root.winfo_height() - height) // 2
    dialog.geometry(f"{width}x{height}+{x_position}+{y_position}")

    label = tk.Label(dialog, text="关闭程序", font=("", 13), bg='#C7EDCC', fg='#333333')
    label.pack(pady=(18, 12))

    button_frame = tk.Frame(dialog, bg='#C7EDCC')
    button_frame.pack(fill='x', padx=16, pady=(0, 18))
    button_frame.grid_columnconfigure(0, weight=1, uniform='dialog-buttons', minsize=112)
    button_frame.grid_columnconfigure(1, weight=1, uniform='dialog-buttons', minsize=112)

    minimize_button = tk.Button(
        button_frame,
        text="最小化",
        command=lambda: close_dialog("minimize"),
        font=("", 11),
        bg='#A3DCB1',
        fg='#333333',
        relief='flat',
        bd=0,
        highlightthickness=0,
        width=12,
        height=2,
    )
    minimize_button.grid(row=0, column=0, padx=(0, 10), sticky='ew')
    bind_hover_style(minimize_button)

    exit_button = tk.Button(
        button_frame,
        text="直接退出",
        command=lambda: close_dialog("quit"),
        font=("", 11),
        bg='#A3DCB1',
        fg='#333333',
        relief='flat',
        bd=0,
        highlightthickness=0,
        width=12,
        height=2,
    )
    exit_button.grid(row=0, column=1, padx=(10, 0), sticky='ew')
    bind_hover_style(exit_button)

    dialog.transient(root)
    dialog.grab_set()
    dialog.deiconify()
    minimize_button.focus_set()
    root.wait_window(dialog)

    if result["action"] == "minimize":
        hide_window_to_tray()
    elif result["action"] == "quit":
        quit_application()


def quit_application():
    global float_window

    hide_tray_icon()
    if float_window is not None and float_window.winfo_exists():
        float_window.destroy()
    root.destroy()


def process_tray_actions():
    while True:
        try:
            action = action_queue.get_nowait()
        except queue.Empty:
            break

        if action == "toggle_window":
            if is_root_visible():
                hide_window_to_tray()
            else:
                restore_window()
        elif action == "start_focus":
            start_focus_session()
        elif action == "start_break":
            start_break_session()
        elif action == "quit":
            quit_application()
            return

    if root.winfo_exists():
        root.after(200, process_tray_actions)


def on_root_unmap(event):
    if event.widget == root and root.state() == "iconic":
        root.after(0, hide_window_to_tray)


def validate_input(new_value):
    if new_value.isdigit() and len(new_value) <= 3:
        return True
    elif new_value == "":
        return True
    else:
        return False


if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    root.withdraw()  # 先隐藏窗口，避免窗口闪烁
    root.title(f"{APP_NAME}")
    root.resizable(False, False)  # 禁止改变主窗口大小
    root.configure(bg='#C7EDCC')
    root.iconbitmap(resource_path(ICON_FILE))

    # 获取屏幕宽度和高度
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 设置主窗口的初始位置为屏幕中央
    window_width = 300
    window_height = 240
    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # 提示标签
    label = tk.Label(root, text="专注时长（分钟）", font=("", 11), bg='#C7EDCC', fg='#333333')
    label.place(relx=0.5, rely=0.1, anchor='center')

    # 输入框
    vcmd = (root.register(validate_input), '%P')
    entry = tk.Entry(
        root,
        width=20,
        font=("", 40, "bold"),
        justify='center',
        validate='key',
        validatecommand=vcmd,
        bg='#A3DCB1',
        fg='#333333',
        bd=0,
        highlightthickness=0,
        relief='flat',
    )
    entry.place(relx=0.5, rely=0.4, anchor='center', width=100, height=100)
    entry.insert(0, "25")

    def defocus_entry(event):
        if event.widget != entry:
            root.focus()

    root.bind("<Button-1>", defocus_entry)
    root.bind("<Unmap>", on_root_unmap)
    root.protocol("WM_DELETE_WINDOW", confirm_close_action)

    # 鼠标悬停事件
    def on_enter(event):
        start_button.config(bg='#A3DCB1', font=("", 15, "bold"))

    def on_leave(event):
        start_button.config(bg='#A3DCB1', font=("", 15))

    # 开始按钮
    start_button = tk.Button(
        root,
        text="开始",
        font=("", 15),
        width=10,
        height=2,
        command=start_focus_session,
        bg='#A3DCB1',
        fg='#333333',
        relief='flat',
        bd=0,
        highlightthickness=0,
    )
    start_button.place(relx=0.5, rely=0.75, anchor='center')
    start_button.bind("<Enter>", on_enter)
    start_button.bind("<Leave>", on_leave)

    # 创建关于按钮（使用问号图标）
    about_button = tk.Button(
        root,
        text="?",
        font=("", 12),
        width=2,
        height=1,
        command=show_about,
        bg='#A3DCB1',
        fg='#333333',
        relief='flat',
        bd=0,
        highlightthickness=0,
    )
    about_button.place(relx=0.9, rely=0.1, anchor='center')

    root.update_idletasks()
    show_tray_icon()
    root.deiconify()
    root.after(200, process_tray_actions)
    root.mainloop()
