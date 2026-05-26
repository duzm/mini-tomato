import tkinter as tk

from .constant import DEFAULT_BREAK_TIME, DEFAULT_WORK_TIME
from .settings_store import set_saved_minutes
from .window_position import get_float_position, remember_float_position


class TimerController:
    def __init__(self, ctx, float_window_size, show_info_dialog):
        self.ctx = ctx
        self.float_window_size = float_window_size
        self.show_info_dialog = show_info_dialog
        self.on_state_change = lambda: None

    def set_on_state_change(self, callback):
        self.on_state_change = callback

    def get_entry_minutes(self, entry_widget, default_seconds):
        value = entry_widget.get().strip()
        if not value:
            return default_seconds // 60
        try:
            minutes = int(value)
        except ValueError:
            return default_seconds // 60
        return minutes if minutes > 0 else default_seconds // 60

    def get_focus_minutes(self):
        return self.get_entry_minutes(self.ctx.focus_entry, DEFAULT_WORK_TIME)

    def get_break_minutes(self):
        return self.get_entry_minutes(self.ctx.break_entry, DEFAULT_BREAK_TIME)

    def save_duration_settings(self, focus_minutes, break_minutes):
        set_saved_minutes(self.ctx.app_settings, "focus_minutes", focus_minutes)
        set_saved_minutes(self.ctx.app_settings, "break_minutes", break_minutes)

    def start_focus_session(self):
        focus_minutes = self.get_focus_minutes()
        break_minutes = self.get_break_minutes()
        self.save_duration_settings(focus_minutes, break_minutes)
        self.start_timer(work_time=focus_minutes * 60, break_time=break_minutes * 60)

    def start_break_session(self):
        focus_minutes = self.get_focus_minutes()
        break_minutes = self.get_break_minutes()
        self.save_duration_settings(focus_minutes, break_minutes)
        self.start_timer(work_time=focus_minutes * 60, break_time=break_minutes * 60, is_work_time=False)

    def update_timer_controls(self):
        root = self.ctx.root
        if self.ctx.start_button is not None and root is not None and root.winfo_exists():
            if self.ctx.timer_active:
                self.ctx.start_button.config(text="停止", command=self.stop_current_timer)
            else:
                self.ctx.start_button.config(text="开始", command=self.start_focus_session)
        self.on_state_change()

    def clear_timer_state(self, cancel_job=True, destroy_window=True):
        root = self.ctx.root

        self.ctx.timer_active = False
        self.ctx.current_phase = None

        if cancel_job and self.ctx.timer_job is not None and root is not None and root.winfo_exists():
            try:
                root.after_cancel(self.ctx.timer_job)
            except tk.TclError:
                pass
        self.ctx.timer_job = None

        if destroy_window and self.ctx.float_window is not None:
            remember_float_position(self.ctx)
            try:
                if self.ctx.float_window.winfo_exists():
                    self.ctx.float_window.destroy()
            except tk.TclError:
                pass
        self.ctx.float_window = None
        self.update_timer_controls()

    def stop_current_timer(self):
        self.clear_timer_state()

    def start_timer(self, work_time=DEFAULT_WORK_TIME, break_time=DEFAULT_BREAK_TIME, is_work_time=True):
        root = self.ctx.root
        self.clear_timer_state()
        self.ctx.timer_active = True
        self.ctx.current_phase = "work" if is_work_time else "break"

        float_window = tk.Toplevel(root)
        self.ctx.float_window = float_window
        float_window.overrideredirect(True)
        float_window.attributes("-topmost", True)
        float_window.attributes("-alpha", 0.5)

        window_width, window_height = self.float_window_size
        x_position, y_position = get_float_position(root, self.ctx.app_settings, self.float_window_size)
        float_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        label = tk.Label(float_window, text="", font=("Helvetica", 48))
        label.pack(expand=True)

        def start_move(event):
            float_window.x = event.x
            float_window.y = event.y

        def do_move(event):
            x = event.x - float_window.x + float_window.winfo_x()
            y = event.y - float_window.y + float_window.winfo_y()
            float_window.geometry(f"+{x}+{y}")

        def finish_move(event):
            remember_float_position(self.ctx)

        float_window.bind("<Button-1>", start_move)
        float_window.bind("<B1-Motion>", do_move)
        float_window.bind("<ButtonRelease-1>", finish_move)
        self.update_timer_controls()

        def countdown(count):
            if not self.ctx.timer_active or self.ctx.float_window is None or not self.ctx.float_window.winfo_exists():
                return

            mins, secs = divmod(count, 60)
            label.config(text='{:02d}:{:02d}'.format(mins, secs))

            if count > 0:
                self.ctx.timer_job = float_window.after(1000, countdown, count - 1)
            else:
                self.clear_timer_state(cancel_job=False)
                if is_work_time:
                    self.show_info_dialog("时间到", "工作时间结束！休息一下吧~")
                    self.start_timer(work_time=work_time, break_time=break_time, is_work_time=False)
                else:
                    self.show_info_dialog("时间到", "休息时间结束！开始新的工作周期")
                    self.start_timer(work_time=work_time, break_time=break_time, is_work_time=True)

        countdown(work_time if is_work_time else break_time)