import queue
import threading
import tkinter as tk
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppContext:
    app_settings: dict
    root: tk.Tk | None = None
    float_window: tk.Toplevel | None = None
    timer_job: str | None = None
    timer_active: bool = False
    current_phase: str | None = None
    focus_entry: tk.Entry | None = None
    break_entry: tk.Entry | None = None
    start_button: tk.Button | None = None
    tray_icon: Any = None
    tray_thread: threading.Thread | None = None
    tray_visible: bool = False
    action_queue: queue.SimpleQueue = field(default_factory=queue.SimpleQueue)
    root_position_job: str | None = None