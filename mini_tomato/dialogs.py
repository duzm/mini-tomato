import tkinter as tk

from .constant import APP_NAME, AUTHOR, GITHUB_URL, VERSION


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


def get_dialog_position(root, width, height):
    if root is not None and root.winfo_exists() and root.state() != "withdrawn":
        return root.winfo_x() + (root.winfo_width() - width) // 2, root.winfo_y() + (root.winfo_height() - height) // 2

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    return (screen_width - width) // 2, (screen_height - height) // 2


def show_info_dialog(root, icon_path, title, message):
    dialog = tk.Toplevel(root)
    dialog.withdraw()
    dialog.title(title)
    dialog.configure(bg='#C7EDCC')
    dialog.resizable(False, False)
    dialog.attributes("-topmost", True)

    try:
        dialog.iconbitmap(icon_path)
    except tk.TclError:
        pass

    width = 320
    height = 170
    x_position, y_position = get_dialog_position(root, width, height)
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


def show_about(root, icon_path):
    about_window = tk.Toplevel(root)
    about_window.withdraw()
    about_window.title("关于")
    about_window.configure(bg='#C7EDCC')

    try:
        about_window.iconbitmap(icon_path)
    except tk.TclError:
        pass

    window_width = 300
    window_height = 240
    x_position = root.winfo_x() + (root.winfo_width() - window_width) // 2
    y_position = root.winfo_y() + (root.winfo_height() - window_height) // 2
    about_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
    about_window.resizable(False, False)

    about_text = f"""
{APP_NAME} {VERSION}

一个简单而实用的番茄工作法计时器。
特点：悬浮半透明小窗口。

作者: {AUTHOR}
GitHub: {GITHUB_URL}
"""
    label = tk.Label(about_window, text=about_text, bg='#C7EDCC', fg='#333333', justify=tk.LEFT, padx=20, pady=0)
    label.pack()

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

    about_window.transient(root)
    about_window.grab_set()
    about_window.deiconify()
    root.wait_window(about_window)


def confirm_close_action(root, icon_path, on_minimize, on_quit):
    dialog = tk.Toplevel(root)
    dialog.withdraw()
    dialog.title("关闭程序")
    dialog.configure(bg='#C7EDCC')
    dialog.resizable(False, False)

    try:
        dialog.iconbitmap(icon_path)
    except tk.TclError:
        pass

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
        on_minimize()
    elif result["action"] == "quit":
        on_quit()