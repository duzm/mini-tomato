"""
@Author: duzm
@Time: 2025年2月22日
@Description: 番茄钟。特点：悬浮半透明小窗口倒计时。
"""

import os
import sys
import tkinter as tk

from .app_state import AppContext
from .constant import APP_NAME, DEFAULT_BREAK_TIME, DEFAULT_WORK_TIME, ICON_FILE
from .dialogs import bind_hover_style, confirm_close_action, show_about, show_info_dialog
from .settings_store import get_saved_minutes, load_settings
from .timer_controller import TimerController
from .tray_controller import TrayController
from .window_position import get_root_position, remember_root_position, schedule_root_position_save


WINDOW_SIZE = (360, 360)
FLOAT_WINDOW_SIZE = (200, 100)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def validate_input(new_value):
    if new_value.isdigit() and len(new_value) <= 3:
        return True
    if new_value == "":
        return True
    return False


def main():
    ctx = AppContext(app_settings=load_settings())
    icon_path = resource_path(ICON_FILE)

    root = tk.Tk()
    ctx.root = root
    root.withdraw()
    root.title(f"{APP_NAME}")
    root.resizable(False, False)
    root.configure(bg='#C7EDCC')

    try:
        root.iconbitmap(icon_path)
    except tk.TclError:
        pass

    window_width, window_height = WINDOW_SIZE
    x_position, y_position = get_root_position(root, ctx.app_settings, WINDOW_SIZE)
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    content_width = 132
    input_height = 64
    button_height = 46

    focus_label = tk.Label(root, text="专注时长（分钟）", font=("", 11), bg='#C7EDCC', fg='#333333')
    focus_label.place(relx=0.5, rely=0.15, anchor='center')

    break_label = tk.Label(root, text="休息时长（分钟）", font=("", 11), bg='#C7EDCC', fg='#333333')
    break_label.place(relx=0.5, rely=0.45, anchor='center')

    vcmd = (root.register(validate_input), '%P')
    ctx.focus_entry = tk.Entry(
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
    ctx.focus_entry.place(relx=0.5, rely=0.28, anchor='center', width=content_width, height=input_height)
    ctx.focus_entry.insert(0, str(get_saved_minutes(ctx.app_settings, "focus_minutes", DEFAULT_WORK_TIME)))

    ctx.break_entry = tk.Entry(
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
    ctx.break_entry.place(relx=0.5, rely=0.58, anchor='center', width=content_width, height=input_height)
    ctx.break_entry.insert(0, str(get_saved_minutes(ctx.app_settings, "break_minutes", DEFAULT_BREAK_TIME)))

    timer_controller = TimerController(
        ctx,
        float_window_size=FLOAT_WINDOW_SIZE,
        show_info_dialog=lambda title, message: show_info_dialog(root, icon_path, title, message),
    )

    tray_controller = None

    def quit_application():
        remember_root_position(ctx)
        timer_controller.stop_current_timer()
        if tray_controller is not None:
            tray_controller.hide_icon()
        root.destroy()

    tray_controller = TrayController(
        ctx,
        icon_path=icon_path,
        start_focus=timer_controller.start_focus_session,
        start_break=timer_controller.start_break_session,
        stop_timer=timer_controller.stop_current_timer,
        remember_root_position=lambda: remember_root_position(ctx),
        quit_application=quit_application,
    )
    timer_controller.set_on_state_change(tray_controller.refresh_menu)

    def defocus_entry(event):
        if event.widget not in (ctx.focus_entry, ctx.break_entry):
            root.focus()

    root.bind("<Button-1>", defocus_entry)
    root.bind("<Configure>", lambda event: schedule_root_position_save(ctx, event))
    root.bind("<Unmap>", tray_controller.on_root_unmap)
    root.protocol(
        "WM_DELETE_WINDOW",
        lambda: confirm_close_action(root, icon_path, tray_controller.hide_window_to_tray, quit_application),
    )

    ctx.start_button = tk.Button(
        root,
        text="开始",
        font=("", 15),
        command=timer_controller.start_focus_session,
        relief='flat',
        bd=0,
        highlightthickness=0,
    )
    ctx.start_button.place(relx=0.5, rely=0.83, anchor='center', width=content_width, height=button_height)
    bind_hover_style(ctx.start_button, font_size=15)

    about_button = tk.Button(
        root,
        text="?",
        font=("", 12),
        width=2,
        height=1,
        command=lambda: show_about(root, icon_path),
        relief='flat',
        bd=0,
        highlightthickness=0,
    )
    about_button.place(relx=0.88, rely=0.09, anchor='center')
    bind_hover_style(about_button, font_size=12)

    root.update_idletasks()
    timer_controller.update_timer_controls()
    tray_controller.show_icon()
    root.deiconify()
    root.after(200, tray_controller.process_actions)
    root.mainloop()