import json
import os


SETTINGS_DIR_NAME = "MiniTomato"
SETTINGS_FILE_NAME = "settings.json"


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


def save_settings(settings):
    settings_path = get_settings_file_path()
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, ensure_ascii=False, indent=2)


def get_saved_position(settings, key):
    position = settings.get(key)
    if not isinstance(position, dict):
        return None

    x = position.get("x")
    y = position.get("y")
    if isinstance(x, int) and isinstance(y, int):
        return x, y
    return None


def set_saved_position(settings, key, x, y):
    settings[key] = {"x": int(x), "y": int(y)}
    try:
        save_settings(settings)
    except OSError:
        pass


def get_saved_minutes(settings, key, default_seconds):
    default_minutes = default_seconds // 60
    minutes = settings.get(key)
    return minutes if isinstance(minutes, int) and minutes > 0 else default_minutes


def set_saved_minutes(settings, key, minutes):
    settings[key] = int(minutes)
    try:
        save_settings(settings)
    except OSError:
        pass