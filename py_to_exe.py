"""
@author:      duzm
@file:        py_to_exe.py
@time:        2023/8/8 15:05
@description: 将Python脚本打包成EXE文件。
"""

import os
import shutil
import subprocess

from constant import ICON_FILE, VERSION

script_file = "main.py"

output_name = f"MiniTomato-{VERSION}.exe"

# 检查图标文件是否存在
if not os.path.exists(ICON_FILE):
    print(f"图标文件 {ICON_FILE} 不存在，请确保图标文件存在于当前目录中。")
else:
    # 运行 PyInstaller 命令打包脚本
    subprocess.run(
        [
            "pyinstaller",
            "--onefile",
            "--windowed",
            f"--icon={ICON_FILE}",
            f"--name={output_name}",
            "--add-data",
            f"{ICON_FILE};.",
            script_file,
        ]
    )

    # 复制生成的EXE文件为另一个文件，文件名固定为：MiniTomato-latest.exe
    shutil.copy(f"dist/{output_name}", "dist/MiniTomato-latest.exe")
