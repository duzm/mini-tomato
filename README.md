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
3. 运行:
   ```bash
   python main.py
   ```
4. 打包exe:
   ```bash
   python py_to_exe.py
   ```

## 功能说明
- 支持在主窗口分别配置默认专注时长和默认休息时长，并自动保存下次启动继续使用。
- 支持专注和休息两个倒计时阶段，阶段自然结束后会自动切换到下一阶段。
- 支持最小化到系统托盘，并从托盘快速开始专注、休息、停止计时或恢复窗口；仅在倒计时进行中显示“停止计时”。
- 支持在主窗口点击“停止”按钮，立即中断当前计时并关闭倒计时悬浮窗。

## 文件说明
- `main.py`: 主程序
- `constant.py`: 常量配置
- `requirements.txt`: 项目依赖
- `py_to_exe.py`: 打包脚本
- `icon.ico`: 程序图标

## 许可证
本项目基于 MIT 许可证开源。