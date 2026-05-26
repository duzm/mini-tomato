"""
@author:      duzm
@file:        py_to_exe.py
@time:        2023/8/8 15:05
@description: 将Python脚本打包成EXE文件。
"""

import os
import shutil
import subprocess
import sys

from mini_tomato.constant import ICON_FILE, VERSION

script_file = "main.py"

output_name = f"MiniTomato-{VERSION}.exe"

def main():
    if not os.path.exists(ICON_FILE):
        print(f"图标文件 {ICON_FILE} 不存在，请确保图标文件存在于当前目录中。")
        return

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--windowed",
            f"--icon={ICON_FILE}",
            f"--name={output_name}",
            "--add-data",
            f"{ICON_FILE};.",
            script_file,
        ],
        check=True,
    )

    shutil.copy(f"dist/{output_name}", "dist/MiniTomato-latest.exe")


if __name__ == "__main__":
    main()
