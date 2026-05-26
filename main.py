"""
@Author: duzm
@Time: 2025年2月22日
@Description: 番茄钟。特点：悬浮半透明小窗口倒计时。
"""

import os
import queue
import json
import sys
import threading
import tkinter as tk

import pystray
from PIL import Image

if sys.platform == "win32":
    from pystray import _win32 as pystray_win32

from constant import APP_NAME, AUTHOR, DEFAULT_BREAK_TIME, DEFAULT_WORK_TIME, GITHUB_URL, ICON_FILE, VERSION

# 全局变量，用于跟踪当前的悬浮窗口
float_window = None
timer_job = None
timer_active = False
current_phase = None
root = None
focus_entry = None
break_entry = None
start_button = None
tray_icon = None
tray_thread = None
tray_visible = False
action_queue = queue.SimpleQueue()
root_position_job = None

SETTINGS_DIR_NAME = "MiniTomato"
SETTINGS_FILE_NAME = "settings.json"
WINDOW_SIZE = (360, 360)
FLOAT_WINDOW_SIZE = (200, 100)


def get_settings_file_path():
    base_dir = os.getenv("APPDATA") or os.path.expanduser("~")
    return os.path.join(base_dir, SETTINGS_DIR_NAME, SETTINGS_FILE_NAME)


def load_settings():
    settings_path = get_settings_file_path()
    if not os.path.exists(settings_path):
        return {}

    try:
        with open(settings_path, "r", encoding="utf-8") as settings_file:
            data = json.load(settings_file)
    except (OSError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def save_settings():
    settings_path = get_settings_file_path()
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as settings_file:
        json.dump(app_settings, settings_file, ensure_ascii=False, indent=2)


def get_saved_position(key):
    position = app_settings.get(key)
    if not isinstance(position, dict):
        return None

    x = position.get("x")
    y = position.get("y")
    if isinstance(x, int) and isinstance(y, int):
        return x, y
    return None


def set_saved_position(key, x, y):
    app_settings[key] = {"x": int(x), "y": int(y)}
    try:
        save_settings()
    except OSError:
        pass


def get_saved_minutes(key, default_seconds):
    default_minutes = default_seconds // 60
    minutes = app_settings.get(key)
    return minutes if isinstance(minutes, int) and minutes > 0 else default_minutes


def set_saved_minutes(key, minutes):
    app_settings[key] = int(minutes)
    try:
        save_settings()
    except OSError:
        pass


def get_virtual_screen_bounds():
    min_x = root.winfo_vrootx()
    min_y = root.winfo_vrooty()
    width = root.winfo_vrootwidth()
    height = root.winfo_vrootheight()

    if width <= 1 or height <= 1:
        min_x = 0
        min_y = 0
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()

    return min_x, min_y, width, height


def clamp_position(x, y, window_width, window_height, min_x, min_y, screen_width, screen_height):
    max_x = max(min_x + screen_width - window_width, min_x)
    max_y = max(min_y + screen_height - window_height, min_y)
    return min(max(x, min_x), max_x), min(max(y, min_y), max_y)


def get_default_root_position():
    window_width, window_height = WINDOW_SIZE
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    return (screen_width - window_width) // 2, (screen_height - window_height) // 2


def get_root_position():
    saved_position = get_saved_position("root_position")
    x_position, y_position = saved_position if saved_position is not None else get_default_root_position()
    min_x, min_y, screen_width, screen_height = get_virtual_screen_bounds()
    return clamp_position(
        x_position, y_position, WINDOW_SIZE[0], WINDOW_SIZE[1], min_x, min_y, screen_width, screen_height
    )


def get_default_float_position():
    window_width, window_height = FLOAT_WINDOW_SIZE
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    return screen_width - window_width - 50, screen_height - window_height - 70


def get_float_position():
    saved_position = get_saved_position("float_position")
    x_position, y_position = saved_position if saved_position is not None else get_default_float_position()
    min_x, min_y, screen_width, screen_height = get_virtual_screen_bounds()
    return clamp_position(
        x_position, y_position, FLOAT_WINDOW_SIZE[0], FLOAT_WINDOW_SIZE[1], min_x, min_y, screen_width, screen_height
    )


def remember_root_position():
    if root is None or not root.winfo_exists() or root.state() != "normal":
        return
    set_saved_position("root_position", root.winfo_x(), root.winfo_y())


def remember_float_position():
    if float_window is None:
        return

    try:
        if float_window.winfo_exists():
            set_saved_position("float_position", float_window.winfo_x(), float_window.winfo_y())
    except tk.TclError:
        pass


def schedule_root_position_save(event=None):
    global root_position_job

    if root is None or not root.winfo_exists() or root.state() != "normal":
        return

    if root_position_job is not None:
        try:
            root.after_cancel(root_position_job)
        except tk.TclError:
            pass

    root_position_job = root.after(200, remember_root_position)


app_settings = load_settings()


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
                    pystray_win32.win32.TPM_LEFTALIGN
                    | pystray_win32.win32.TPM_BOTTOMALIGN
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


def bind_hover_style(button, font_size=11):
    normal_bg = '#A3DCB1'
    hover_bg = '#8DCEA0'
    pressed_bg = '#7CC08F'

    button.config(
        bg=normal_bg,
        fg='#333333',
        font=("", font_size),
        activebackground=pressed_bg,
        activeforeground='#333333',
        disabledforeground='#6B6B6B',
        highlightbackground=normal_bg,
        highlightcolor=hover_bg,
        takefocus=False,
    )

    def on_enter(event):
        event.widget.config(bg=hover_bg, font=("", font_size, "bold"))

    def on_leave(event):
        event.widget.config(bg=normal_bg, font=("", font_size))

    def on_press(event):
        event.widget.config(bg=pressed_bg, font=("", font_size, "bold"))

    def on_release(event):
        widget = event.widget
        x_root = widget.winfo_pointerx()
        y_root = widget.winfo_pointery()
        inside_x = 0 <= x_root - widget.winfo_rootx() <= widget.winfo_width()
        inside_y = 0 <= y_root - widget.winfo_rooty() <= widget.winfo_height()
        if inside_x and inside_y:
            widget.config(bg=hover_bg, font=("", font_size, "bold"))
        else:
            widget.config(bg=normal_bg, font=("", font_size))

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    button.bind("<ButtonPress-1>", on_press)
    button.bind("<ButtonRelease-1>", on_release)


def get_dialog_position(width, height):
    if root is not None and root.winfo_exists() and root.state() != "withdrawn":
        return root.winfo_x() + (root.winfo_width() - width) // 2, root.winfo_y() + (root.winfo_height() - height) // 2

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    return (screen_width - width) // 2, (screen_height - height) // 2


def show_info_dialog(title, message):
    dialog = tk.Toplevel(root)
    dialog.withdraw()
    dialog.title(title)
    dialog.configure(bg='#C7EDCC')
    dialog.resizable(False, False)
    dialog.attributes("-topmost", True)

    try:
        dialog.iconbitmap(resource_path(ICON_FILE))
    except tk.TclError:
        pass

    width = 320
    height = 170
    x_position, y_position = get_dialog_position(width, height)
    dialog.geometry(f"{width}x{height}+{x_position}+{y_position}")

    def close_dialog(event=None):
        dialog.destroy()

    title_label = tk.Label(dialog, text=title, font=("", 13), bg='#C7EDCC', fg='#333333')
    title_label.pack(pady=(18, 10))

    message_label = tk.Label(
        dialog, text=message, font=("", 11), bg='#C7EDCC', fg='#333333', wraplength=260, justify='center'
    )
    message_label.pack(padx=24)

    ok_button = tk.Button(
        dialog,
        text="确定",
        command=close_dialog,
        font=("", 11),
        relief='flat',
        bd=0,
        highlightthickness=0,
        width=12,
        height=2,
    )
    ok_button.pack(pady=(20, 18))
    bind_hover_style(ok_button)

    if root is not None and root.winfo_exists() and root.state() != "withdrawn":
        dialog.transient(root)

    dialog.protocol("WM_DELETE_WINDOW", close_dialog)
    dialog.bind("<Return>", close_dialog)
    dialog.bind("<Escape>", close_dialog)
    dialog.grab_set()
    dialog.deiconify()
    dialog.lift()
    ok_button.focus_set()
    root.wait_window(dialog)


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
        about_window,
        text="确定",
        command=about_window.destroy,
        width=12,
        height=2,
        relief='flat',
        bd=0,
        highlightthickness=0,
    )

    ok_button.pack(pady=(10, 14))
    bind_hover_style(ok_button)

    # 设置模态窗口
    about_window.transient(root)
    about_window.grab_set()
    about_window.deiconify()
    root.wait_window(about_window)


def get_entry_minutes(entry_widget, default_seconds):
    value = entry_widget.get().strip()
    if not value:
        return default_seconds // 60
    try:
        minutes = int(value)
    except ValueError:
        return default_seconds // 60
    return minutes if minutes > 0 else default_seconds // 60


def get_focus_minutes():
    return get_entry_minutes(focus_entry, DEFAULT_WORK_TIME)


def get_break_minutes():
    return get_entry_minutes(break_entry, DEFAULT_BREAK_TIME)


def save_duration_settings(focus_minutes, break_minutes):
    set_saved_minutes("focus_minutes", focus_minutes)
    set_saved_minutes("break_minutes", break_minutes)


def start_focus_session():
    focus_minutes = get_focus_minutes()
    break_minutes = get_break_minutes()
    save_duration_settings(focus_minutes, break_minutes)
    start_timer(work_time=focus_minutes * 60, break_time=break_minutes * 60)


def start_break_session():
    focus_minutes = get_focus_minutes()
    break_minutes = get_break_minutes()
    save_duration_settings(focus_minutes, break_minutes)
    start_timer(work_time=focus_minutes * 60, break_time=break_minutes * 60, is_work_time=False)


def update_timer_controls():
    if start_button is not None and root is not None and root.winfo_exists():
        if timer_active:
            start_button.config(text="停止", command=stop_current_timer)
        else:
            start_button.config(text="开始", command=start_focus_session)
    refresh_tray_menu()


def clear_timer_state(cancel_job=True, destroy_window=True):
    global float_window, timer_job, timer_active, current_phase

    timer_active = False
    current_phase = None

    if cancel_job and timer_job is not None and root is not None and root.winfo_exists():
        try:
            root.after_cancel(timer_job)
        except tk.TclError:
            pass
    timer_job = None

    if destroy_window and float_window is not None:
        remember_float_position()
        try:
            if float_window.winfo_exists():
                float_window.destroy()
        except tk.TclError:
            pass
    float_window = None
    update_timer_controls()


def stop_current_timer():
    clear_timer_state()


def start_timer(work_time=DEFAULT_WORK_TIME, break_time=DEFAULT_BREAK_TIME, is_work_time=True):
    global float_window, timer_job, timer_active, current_phase

    clear_timer_state()
    timer_active = True
    current_phase = "work" if is_work_time else "break"

    # 创建新的悬浮窗口
    float_window = tk.Toplevel(root)
    float_window.overrideredirect(True)  # 去掉窗口边框
    float_window.attributes("-topmost", True)  # 窗口置顶
    float_window.attributes("-alpha", 0.5)  # 设置窗口透明度

    window_width, window_height = FLOAT_WINDOW_SIZE
    x_position, y_position = get_float_position()
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

    def finish_move(event):
        remember_float_position()

    float_window.bind("<Button-1>", start_move)
    float_window.bind("<B1-Motion>", do_move)
    float_window.bind("<ButtonRelease-1>", finish_move)
    update_timer_controls()

    # 倒计时功能
    def countdown(count):
        global timer_job

        if not timer_active or float_window is None or not float_window.winfo_exists():
            return

        mins, secs = divmod(count, 60)
        time_format = '{:02d}:{:02d}'.format(mins, secs)
        label.config(text=time_format)

        if count > 0:
            timer_job = float_window.after(1000, countdown, count - 1)
        else:
            clear_timer_state(cancel_job=False)
            if is_work_time:
                show_info_dialog("时间到", "工作时间结束！休息一下吧~")
                start_timer(work_time=work_time, break_time=break_time, is_work_time=False)  # 开始休息时间
            else:
                show_info_dialog("时间到", "休息时间结束！开始新的工作周期")
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


def is_timer_active(item=None):
    return timer_active


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
        pystray.MenuItem("停止计时", enqueue_tray_action("stop_timer"), visible=is_timer_active),
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
    remember_root_position()
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
    remember_root_position()
    stop_current_timer()
    hide_tray_icon()
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
        elif action == "stop_timer":
            stop_current_timer()
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

    window_width, window_height = WINDOW_SIZE
    x_position, y_position = get_root_position()
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    content_width = 132
    input_height = 64
    button_height = 46

    # 提示标签
    focus_label = tk.Label(root, text="专注时长（分钟）", font=("", 11), bg='#C7EDCC', fg='#333333')
    focus_label.place(relx=0.5, rely=0.15, anchor='center')

    break_label = tk.Label(root, text="休息时长（分钟）", font=("", 11), bg='#C7EDCC', fg='#333333')
    break_label.place(relx=0.5, rely=0.45, anchor='center')

    # 输入框
    vcmd = (root.register(validate_input), '%P')
    focus_entry = tk.Entry(
        root,
        width=20,
        font=("", 26, "bold"),
        justify='center',
        validate='key',
        validatecommand=vcmd,
        bg='#A3DCB1',
        fg='#333333',
        bd=0,
        highlightthickness=0,
        relief='flat',
    )
    focus_entry.place(relx=0.5, rely=0.28, anchor='center', width=content_width, height=input_height)
    focus_entry.insert(0, str(get_saved_minutes("focus_minutes", DEFAULT_WORK_TIME)))

    break_entry = tk.Entry(
        root,
        width=20,
        font=("", 26, "bold"),
        justify='center',
        validate='key',
        validatecommand=vcmd,
        bg='#A3DCB1',
        fg='#333333',
        bd=0,
        highlightthickness=0,
        relief='flat',
    )
    break_entry.place(relx=0.5, rely=0.58, anchor='center', width=content_width, height=input_height)
    break_entry.insert(0, str(get_saved_minutes("break_minutes", DEFAULT_BREAK_TIME)))

    def defocus_entry(event):
        if event.widget not in (focus_entry, break_entry):
            root.focus()

    root.bind("<Button-1>", defocus_entry)
    root.bind("<Configure>", schedule_root_position_save)
    root.bind("<Unmap>", on_root_unmap)
    root.protocol("WM_DELETE_WINDOW", confirm_close_action)

    # 鼠标悬停事件
    # 开始按钮
    start_button = tk.Button(
        root, text="开始", font=("", 15), command=start_focus_session, relief='flat', bd=0, highlightthickness=0
    )
    start_button.place(relx=0.5, rely=0.83, anchor='center', width=content_width, height=button_height)
    bind_hover_style(start_button, font_size=15)

    # 创建关于按钮（使用问号图标）
    about_button = tk.Button(
        root, text="?", font=("", 12), width=2, height=1, command=show_about, relief='flat', bd=0, highlightthickness=0
    )
    about_button.place(relx=0.88, rely=0.09, anchor='center')
    bind_hover_style(about_button, font_size=12)

    root.update_idletasks()
    update_timer_controls()
    show_tray_icon()
    root.deiconify()
    root.after(200, process_tray_actions)
    root.mainloop()
