import tkinter as tk

from .settings_store import get_saved_position, set_saved_position


ROOT_POSITION_KEY = "root_position"
FLOAT_POSITION_KEY = "float_position"


def get_virtual_screen_bounds(root):
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


def get_default_root_position(root, window_size):
    window_width, window_height = window_size
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    return (screen_width - window_width) // 2, (screen_height - window_height) // 2


def get_root_position(root, settings, window_size):
    saved_position = get_saved_position(settings, ROOT_POSITION_KEY)
    x_position, y_position = saved_position if saved_position is not None else get_default_root_position(root, window_size)
    min_x, min_y, screen_width, screen_height = get_virtual_screen_bounds(root)
    return clamp_position(x_position, y_position, window_size[0], window_size[1], min_x, min_y, screen_width, screen_height)


def get_default_float_position(root, window_size):
    window_width, window_height = window_size
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    return screen_width - window_width - 50, screen_height - window_height - 70


def get_float_position(root, settings, window_size):
    saved_position = get_saved_position(settings, FLOAT_POSITION_KEY)
    x_position, y_position = saved_position if saved_position is not None else get_default_float_position(root, window_size)
    min_x, min_y, screen_width, screen_height = get_virtual_screen_bounds(root)
    return clamp_position(x_position, y_position, window_size[0], window_size[1], min_x, min_y, screen_width, screen_height)


def remember_root_position(ctx):
    root = ctx.root
    if root is None or not root.winfo_exists() or root.state() != "normal":
        return
    set_saved_position(ctx.app_settings, ROOT_POSITION_KEY, root.winfo_x(), root.winfo_y())


def remember_float_position(ctx):
    if ctx.float_window is None:
        return

    try:
        if ctx.float_window.winfo_exists():
            set_saved_position(ctx.app_settings, FLOAT_POSITION_KEY, ctx.float_window.winfo_x(), ctx.float_window.winfo_y())
    except tk.TclError:
        pass


def schedule_root_position_save(ctx, event=None):
    root = ctx.root
    if root is None or not root.winfo_exists() or root.state() != "normal":
        return

    if ctx.root_position_job is not None:
        try:
            root.after_cancel(ctx.root_position_job)
        except tk.TclError:
            pass

    ctx.root_position_job = root.after(200, lambda: remember_root_position(ctx))