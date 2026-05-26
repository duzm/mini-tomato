import queue
import sys
import threading

import pystray
from PIL import Image

from .constant import APP_NAME

if sys.platform == "win32":
    from pystray import _win32 as pystray_win32


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


class TrayController:
    def __init__(self, ctx, icon_path, start_focus, start_break, stop_timer, remember_root_position, quit_application):
        self.ctx = ctx
        self.icon_path = icon_path
        self.start_focus = start_focus
        self.start_break = start_break
        self.stop_timer = stop_timer
        self.remember_root_position = remember_root_position
        self.quit_application = quit_application

    def enqueue_tray_action(self, action):
        def callback(icon, item):
            self.ctx.action_queue.put(action)

        return callback

    def is_root_visible(self):
        root = self.ctx.root
        return root is not None and root.winfo_exists() and root.state() != "withdrawn"

    def get_window_toggle_text(self, item=None):
        return "最小化窗口" if self.is_root_visible() else "显示窗口"

    def is_timer_active(self, item=None):
        return self.ctx.timer_active

    def refresh_menu(self):
        if self.ctx.tray_icon is not None:
            self.ctx.tray_icon.update_menu()

    def create_tray_image(self):
        return Image.open(self.icon_path)

    def create_tray_menu(self):
        return pystray.Menu(
            pystray.MenuItem(self.get_window_toggle_text, self.enqueue_tray_action("toggle_window"), default=True, visible=False),
            pystray.MenuItem(self.get_window_toggle_text, self.enqueue_tray_action("toggle_window")),
            pystray.MenuItem("开始专注", self.enqueue_tray_action("start_focus")),
            pystray.MenuItem("开始休息", self.enqueue_tray_action("start_break")),
            pystray.MenuItem("停止计时", self.enqueue_tray_action("stop_timer"), visible=self.is_timer_active),
            pystray.MenuItem("退出", self.enqueue_tray_action("quit")),
        )

    def ensure_tray_icon(self):
        if self.ctx.tray_icon is not None:
            return self.ctx.tray_icon

        self.ctx.tray_icon = TrayIcon(APP_NAME, self.create_tray_image(), APP_NAME, self.create_tray_menu())
        self.ctx.tray_thread = threading.Thread(target=self.ctx.tray_icon.run, daemon=True)
        self.ctx.tray_thread.start()
        return self.ctx.tray_icon

    def show_icon(self):
        self.ensure_tray_icon()
        if self.ctx.tray_icon is not None:
            self.ctx.tray_icon.visible = True
            self.ctx.tray_visible = True
            self.refresh_menu()

    def hide_icon(self):
        if self.ctx.tray_icon is not None:
            self.ctx.tray_icon.stop()
            self.ctx.tray_icon = None
            self.ctx.tray_thread = None
        self.ctx.tray_visible = False

    def hide_window_to_tray(self):
        self.remember_root_position()
        root = self.ctx.root
        if root.winfo_exists() and root.state() != "withdrawn":
            root.withdraw()
        self.show_icon()
        self.refresh_menu()

    def restore_window(self):
        root = self.ctx.root
        if not root.winfo_exists():
            return
        self.show_icon()
        root.deiconify()
        root.state("normal")
        root.lift()
        root.focus_force()
        self.refresh_menu()

    def process_actions(self):
        root = self.ctx.root

        while True:
            try:
                action = self.ctx.action_queue.get_nowait()
            except queue.Empty:
                break

            if action == "toggle_window":
                if self.is_root_visible():
                    self.hide_window_to_tray()
                else:
                    self.restore_window()
            elif action == "start_focus":
                self.start_focus()
            elif action == "start_break":
                self.start_break()
            elif action == "stop_timer":
                self.stop_timer()
            elif action == "quit":
                self.quit_application()
                return

        if root.winfo_exists():
            root.after(200, self.process_actions)

    def on_root_unmap(self, event):
        root = self.ctx.root
        if event.widget == root and root.state() == "iconic":
            root.after(0, self.hide_window_to_tray)