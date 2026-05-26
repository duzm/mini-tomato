# 迷你番茄钟 (Mini-Tomato)

Windows平台上一个可自由拖动的悬浮半透明小窗番茄工作法计时器，支持最小化到系统托盘，并通过托盘菜单快速开始专注、休息、停止计时或恢复窗口。

![演示](./images/demo.gif)

## 下载
你可以从 [GitHub Releases](https://github.com/duzm/mini-tomato/releases) 页面下载最新的 `exe` 文件。

## 快速开始
1. 进入项目目录
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行：
   ```bash
   python main.py
   ```
4. 打包 exe：
   ```bash
   python py_to_exe.py
   ```

建议优先在虚拟环境中执行以上命令。打包脚本会使用当前 Python 解释器调用 PyInstaller，因此在什么环境里执行，就会使用那个环境里的依赖。

## 功能说明
- 支持在主窗口分别配置默认专注时长和默认休息时长，并自动保存下次启动继续使用。
- 支持专注和休息两个倒计时阶段，阶段自然结束后会自动切换到下一阶段。
- 支持最小化到系统托盘，并从托盘快速开始专注、休息、停止计时或恢复窗口；仅在倒计时进行中显示“停止计时”。
- 支持在主窗口点击“停止”按钮，立即中断当前计时并关闭倒计时悬浮窗。

## 项目结构
```text
mini-tomato/
├─ main.py                 # 根入口，仅转发到 mini_tomato.app:main
├─ py_to_exe.py            # 打包脚本
├─ requirements.txt        # Python 依赖
├─ icon.ico                # 程序图标
├─ images/                 # README 资源
└─ mini_tomato/            # 业务代码包
   ├─ __init__.py
   ├─ app.py               # 应用启动与界面编排
   ├─ app_state.py         # 运行时状态对象
   ├─ constant.py          # 应用常量
   ├─ dialogs.py           # 对话框与按钮样式
   ├─ settings_store.py    # 设置持久化
   ├─ timer_controller.py  # 计时控制
   ├─ tray_controller.py   # 系统托盘控制
   └─ window_position.py   # 窗口位置恢复与边界处理
```

## 运行说明
- 启动入口是 `main.py`，它会调用 `mini_tomato.app` 中的 `main()`。
- 运行时会在 `%APPDATA%/MiniTomato/settings.json` 中保存专注时长、休息时长以及主窗口和悬浮窗位置。
- 如果你在工作区中使用虚拟环境，建议显式使用对应解释器运行，例如 Windows 下的 `.venv/Scripts/python.exe`。

## 打包说明
- 执行 `python py_to_exe.py` 会生成 `dist/MiniTomato-版本号.exe`，并额外复制一份 `dist/MiniTomato-latest.exe`。
- `py_to_exe.py` 仅在直接执行时才会触发打包；被导入时不会产生副作用。
- 打包脚本通过 `python -m PyInstaller` 调用当前解释器环境中的 PyInstaller，避免误用系统 Python。

## 许可证
本项目基于 MIT 许可证开源。