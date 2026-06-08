# -*- coding: utf-8 -*-
import sys
import os
import hashlib
import time
import socket
import subprocess
import json
import warnings
import ctypes
import webbrowser
from weakref import ref
from headers import get_headers_by_selection
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QProgressBar, QLabel, QMessageBox, QFileDialog
from PyQt6.QtCore import pyqtSlot, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QFontDatabase, QPen
from PyQt6 import QtWidgets, QtCore
from icon_module import set_application_icon
from ui import Ui_MainWindow # 请确保已经正确导入了你的UI类
from jindu import ProgressDialog
from async_downloader import download_manager
from PyQt6.QtCore import qInstallMessageHandler, QtMsgType

def qt_message_handler(mode, context, message):
    """
    自定义 Qt 消息拦截器
    用于屏蔽 Windows 下特定的渲染底层报错，保留其他有用的日志
    """
    # 1. 精准屏蔽：如果消息包含这个关键词，直接丢弃，不打印
    if "UpdateLayeredWindowIndirect failed" in message:
        return
    
    # 2. 其他消息：正常打印
    # 为了保持控制台整洁，我们可以简单格式化一下
    mode_str = {
        QtMsgType.QtDebugMsg: "[Debug]",
        QtMsgType.QtInfoMsg: "[Info]",
        QtMsgType.QtWarningMsg: "[Warning]",
        QtMsgType.QtCriticalMsg: "[Critical]",
        QtMsgType.QtFatalMsg: "[Fatal]"
    }.get(mode, "[Log]")
    
    # 打印格式：[Warning] 你的其他报错信息...
    print(f"{mode_str} {message}")

# 3. 安装拦截器 (这行代码必须在创建 QApplication 之前运行)
qInstallMessageHandler(qt_message_handler)

# 过滤掉这个特定的警告
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*")

#启动清洁模式
class SafeNullWriter:
    def write(self, text):
        # 静默处理写入
        return len(text)  # 返回写入的字符数，避免错误
    
    def flush(self):
        # 空刷新
        pass
    
    def isatty(self):
        return False
    
    @property
    def encoding(self):
        return 'utf-8'
    
def get_deterministic_port():
    """根据程序路径生成固定端口"""
    program_path = os.path.abspath(sys.argv[0])
    hash_obj = hashlib.md5(program_path.encode())
    return 10000 + (int(hash_obj.hexdigest()[:8], 16) % 50000)

def check_single_instance():
    base_port = get_deterministic_port()
    
    # 端口尝试顺序：基础端口 -> +100 -> +200 -> 随机端口
    port_attempts = [
        base_port,              # 首选端口
        base_port + 100,        # 第一备用
        base_port + 200,        # 第二备用
    ]
    
    # 如果前三个都被占用，添加一些随机端口
    import random
    for _ in range(3):
        port_attempts.append(random.randint(10000, 60000))
    
    for i, port in enumerate(port_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('localhost', port))
            
            if i > 0:  # 使用了备用端口
                print(f"⚠️ 使用备用端口: {port} (基础端口 {base_port} 被占用)")
            else:
                print(f"✅ 单实例检查成功 - 端口: {port}")
                
            return sock
            
        except socket.error:
            if i == 0:
                # 基础端口被占用，极有可能是程序已在运行
                app = QApplication(sys.argv)
                # PyQt6 中的正确写法
                QMessageBox.critical(
                    None,
                    "程序已在运行", 
                    "程序已经在运行中！\n点击确定退出。",
                    QMessageBox.StandardButton.Ok  
                )
                sys.exit(1)
            continue
    
    # 极端情况：所有端口都被占用
    app = QApplication(sys.argv)
    QMessageBox.critical(
        None,
        "系统错误",
        "无法找到可用端口，请重启系统后重试！",
        QMessageBox.StandardButton.Ok 
    )
    sys.exit(1)

# 使用
lock_socket = check_single_instance()

# ---------- 进度窗口 ----------
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QProgressBar, 
                             QApplication, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, QTimer
start = time.perf_counter()
class GlassSplashWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("初始化中...")
        
        # 1. 设置窗口属性
        # 420x190 是包含阴影区的总大小，实际内容区大约是 400x170
        self.setFixedSize(420, 190) 
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # === 核心防御 ===
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setDisabled(True)
        
        self.setup_ui()
        self.setup_animation() # 初始化动画对象

    def setup_ui(self):
        # 注意：这里我们不再给 self 设置 Layout，而是直接放一个 container
        # 因为 Layout 会强行锁定尺寸，导致无法做缩放动画
        
        # 1. 创建背景容器
        self.container = QFrame(self)
        self.container.setObjectName("SplashContainer")
        self.container.setStyleSheet("""
            QFrame#SplashContainer {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        
        # 2. 添加阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(Qt.GlobalColor.black)
        self.container.setGraphicsEffect(shadow)
        
        # 3. 容器内部布局 (内容布局保持不变)
        inner_layout = QVBoxLayout(self.container)
        inner_layout.setContentsMargins(20, 25, 20, 25)
        inner_layout.setSpacing(15)
        
        # 标题
        app_header = QLabel("🚀 正在跑步加载中...")
        app_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_header.setStyleSheet("""
            QLabel {
                color: #2c3e50; font-size: 18px; font-weight: bold;
                background: transparent; border: none;
            }
        """)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(0, 0, 0, 0.05);
                border: none; border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 3px;
            }
        """)
        
        # 状态信息
        self.status_label = QLabel("正在加载核心模块...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #5a6c7d; font-size: 12px; font-weight: normal;
                background: transparent; border: none;
            }
        """)
        
        inner_layout.addWidget(app_header)
        inner_layout.addWidget(self.progress)
        inner_layout.addWidget(self.status_label)

        # === 关键：初始化时先把容器设为 0 大小，放在中间 ===
        # 这样窗口一出来的时候是"看不见"容器的
        center_x = self.width() // 2
        center_y = self.height() // 2
        self.container.setGeometry(center_x, center_y, 0, 0)

    def setup_animation(self):
        """配置弹出动画"""
        self.anim = QPropertyAnimation(self.container, b"geometry")
        self.anim.setDuration(900) # 动画时长 600ms
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack) # 回弹曲线：会有"Duang"的一下效果
        
        # 计算终点 (留出 10px 阴影边距)
        margin = 10
        final_rect = QRect(margin, margin, self.width() - margin*2, self.height() - margin*2)
        
        # 计算起点 (中心点)
        center_x = self.width() // 2
        center_y = self.height() // 2
        start_rect = QRect(center_x, center_y, 0, 0)
        
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(final_rect)

    def showEvent(self, event):
        """窗口显示时触发动画"""
        super().showEvent(event)
        self.anim.start()

    def update_progress(self, percent, text=None):
        self.progress.setValue(percent)
        if text:
            self.status_label.setText(text)
        QApplication.processEvents()

from PyQt6.QtCore import QThread, pyqtSignal, QEventLoop, QObject

# ---------- 主窗口 ----------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):  
        super().__init__()

        # 基础变量初始化 (极速)
        self.current_format_worker = None
        self.current_download_worker = None
        self.is_fetching_formats = False
        self.progress_dialog = None
        self.dragging = False
        self.drag_position = QPoint()

        set_application_icon(self) 
        
        # UI 骨架创建
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # 信号槽
        self.ui.pushButton_select_cookie.clicked.connect(self.select_cookie_file)
        self.ui.pushButton_select_folder.clicked.connect(self.select_save_folder)
        self.ui.pushButton_download_video.clicked.connect(self.start_download_video)
        self.ui.pushButton_download_audio.clicked.connect(self.start_download_audio)
        self.ui.close_btn.clicked.connect(lambda: self.kill_windows_process_tree())

    def lazy_init(self):
        """
        分步初始化生成器 - 支持异步等待
        """
        # 1. 加载字体
        yield 20, "正在加载界面字体..."
        # ... (字体代码) ...
        
        # 2. 检查 FFmpeg
        yield 40, "正在检查系统环境..."
        self.check_ffmpeg()
        
        # 3. 后续步骤
        yield 90, "正在启动..."
        yield 100, "准备就绪！"

    def show_error(self, title, message, type='error'):
        """
        统一的错误/提示弹窗
        """
        icon = QMessageBox.Icon.Critical if type == 'error' else QMessageBox.Icon.Information
        QMessageBox(icon, title, message, QMessageBox.StandardButton.Ok, None).exec()

    def kill_windows_process_tree(self):
        """Windows下强制杀死进程树"""
        try:
            if os.name == 'nt':  # Windows
                PROCESS_TERMINATE = 1
                handle = ctypes.windll.kernel32.OpenProcess(
                    PROCESS_TERMINATE, False, os.getpid()
                )
                ctypes.windll.kernel32.TerminateProcess(handle, -1)
                ctypes.windll.kernel32.CloseHandle(handle)
            else:
                os.kill(os.getpid(), signal.SIGKILL)
        except:
            os._exit(1)

    def show_error(self, title, message, dialog_type="error"):
        dialog = CustomErrorDialog(self, title, message, dialog_type)
        dialog.exec()

    def mousePressEvent(self, event):
        """只在标题栏区域启用系统原生拖动"""
        if (event.button() == Qt.MouseButton.LeftButton and 
            event.position().y() <= 30):  # 标题栏高度
            self.windowHandle().startSystemMove()
            event.accept()
        else:
            super().mousePressEvent(event)

    def check_ffmpeg(self):
        """
        检查FFmpeg是否可用
        返回: bool - True表示可用，False表示不可用
        """
        # 检查系统PATH中的FFmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=3)
            print("✅ 系统PATH中找到FFmpeg")
            return True
        except:
            pass
        
        # 检查当前目录下的ffmpeg/bin/ffmpeg.exe
        local_ffmpeg = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
        if os.path.exists(local_ffmpeg):
            try:
                subprocess.run([local_ffmpeg, "-version"], capture_output=True, timeout=3)
                # 添加到当前进程的PATH
                os.environ["PATH"] = os.path.dirname(local_ffmpeg) + os.pathsep + os.environ["PATH"]
                print("✅ 本地目录中找到FFmpeg")
                return True
            except:
                pass
        
        # 两个检查都不通过
        self.show_error('错误', '未找到FFmpeg，点击确定后将打开FFmpeg官网下载页面')
        webbrowser.open("https://ffmpeg.org/download.html")
        sys.exit()

    @pyqtSlot()
    def select_save_folder(self):
        """选择视频保存文件夹"""
        options = QFileDialog.Option.DontUseNativeDialog | QFileDialog.Option.ShowDirsOnly
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            '选择视频保存文件夹', 
            '', 
            options=options
        )
        if folder_path:
            self.ui.lineEdit_folder.setText(folder_path)

    @pyqtSlot()
    def select_cookie_file(self):
        """选择Cookie文件"""
        options = QFileDialog.Option.DontUseNativeDialog | QFileDialog.Option.ReadOnly
        cookie_file, _ = QFileDialog.getOpenFileName(
            self, 
            '选择Cookie文件', 
            '', 
            '所有文件 (*);;文本文件 (*.txt);;Netscape格式 (*.txt)', 
            options=options
        )
        if cookie_file:
            self.ui.lineEdit_cookie.setText(cookie_file)

    @pyqtSlot()
    def start_download_video(self):
        """开始下载视频"""
        self.start_download(download_type="video")

    @pyqtSlot()
    def start_download_audio(self):
        """开始下载音频"""
        self.start_download(download_type="audio")

    def get_and_populate_formats_async(self, url, cookies_file=None):
        """异步获取格式信息"""
        if self.is_fetching_formats:
            return False
        
        if not url:
            self.show_error('错误', '请输入视频URL')
            return False
        
        print("🔄 开始异步获取格式信息...")
        self.is_fetching_formats = True
        self.show_loading_state(True)
        
        # 使用下载管理器
        self.current_format_worker = download_manager.fetch_formats(url, cookies_file)
        
        # 连接信号
        self.current_format_worker.signals.formats_ready.connect(self.on_formats_ready)
        self.current_format_worker.signals.error.connect(self.on_format_error)
        self.current_format_worker.signals.finished.connect(self.on_format_finished)
        
        return True
    
    def show_loading_state(self, show=True):
        """显示/隐藏格式获取的加载状态"""
        from PyQt6.QtCore import QTimer
        
        def update_ui():
            if show:
                # 禁用相关控件并显示加载状态
                self.ui.comboBox_resolution.setEnabled(False)
                self.ui.comboBox_resolution.clear()
                self.ui.comboBox_resolution.addItem("🔄 获取格式中...")
                # 可以添加其他加载状态指示，比如禁用下载按钮等
                if hasattr(self.ui, 'pushButton_download'):
                    self.ui.pushButton_download.setEnabled(False)
            else:
                # 启用控件
                self.ui.comboBox_resolution.setEnabled(True)
                if hasattr(self.ui, 'pushButton_download'):
                    self.ui.pushButton_download.setEnabled(True)
        
        # 使用QTimer确保在主线程中更新UI
        QTimer.singleShot(0, update_ui)
    
    def on_formats_ready(self, available_formats):
        """格式信息就绪"""
        print(f"✅ 成功获取 {len(available_formats)} 个格式")
        self.populate_resolution_combo(available_formats)
        self.show_loading_state(False)  # 隐藏加载状态
        self.show_error('提示', f'已获取 {len(available_formats)} 个清晰度选项，请选择')
    
    def on_format_error(self, error_msg):
        """格式获取错误"""
        print(f"❌ 格式获取错误: {error_msg}")
        self.show_loading_state(False)  # 隐藏加载状态
        self.show_error('错误', f'获取格式信息失败: {error_msg}')
    
    def on_format_finished(self, result):
        """格式获取完成"""
        self.is_fetching_formats = False
        self.current_format_worker = None

        # 从下载管理器中移除工作器
        if self.current_format_worker:
            download_manager.remove_worker(self.current_format_worker)
            self.current_format_worker = None
        
        if not result:
            self.populate_resolution_combo([])
    
    def start_download_async(self, download_type, url, cookies_file=None, 
                            output_dir='downloads', start_time=None, 
                            end_time=None, resolution_choice=None):
            """异步开始下载 - 适配新版 ProgressDialog"""
        
            # 1. 基础准备
            system_proxy = self.get_system_proxy()
            headers = self.get_headers_by_selection()

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 2. 创建并显示新版进度对话框
            # 注意：这里我们要保存引用，防止被垃圾回收
            self.progress_dialog = ProgressDialog(self)
            self.progress_dialog.show()

            # === 新增：进度条平滑处理状态变量 ===
            self.download_state = {
                "type": download_type,      # 记录类型
                "pass": 1,                  # 第几遍 (1=视频, 2=音频)
                "last_raw_progress": 0,     # 上一次收到的原始进度
                "is_closing": False         # 是否正在关闭
            }

            # === 新增：添加一个标志位，防止结束流程被打断 ===
            self.is_download_closing = False 
            
            # 可选：连接对话框关闭信号，如果用户手动点×，取消下载
            # self.progress_dialog.rejected.connect(self.cancel_download) 
            
            # 3. 获取 Worker (假设 download_manager 返回的是未启动的 QThread/QRunnable)
            if download_type == "video":
                worker = download_manager.download_video(
                    url, cookies_file, output_dir, start_time, end_time, 
                    resolution_choice, system_proxy, headers
                )
            else:  # audio
                worker = download_manager.download_audio(
                    url, cookies_file, output_dir, start_time, end_time, 
                    resolution_choice, system_proxy, headers
                )

            worker.download_type = download_type
            self.current_download_worker = worker

            # 4. 信号连接 (使用 weakref 保持最佳实践)
            from weakref import ref
            weak_self = ref(self)

            def on_finished(result):
                strong_self = weak_self()
                if strong_self:
                    download_type = getattr(worker, 'download_type', 'video')
                    # 转发给专门的结束处理函数
                    strong_self.handle_download_finished(result, download_type)

            def on_error(error_msg):
                strong_self = weak_self()
                if strong_self:
                    # 转发给专门的错误处理函数
                    strong_self.handle_download_error(error_msg)

            # 连接信号
            worker.signals.progress.connect(self.on_download_progress)
            worker.signals.finished.connect(on_finished)
            worker.signals.error.connect(on_error)

            # 5. 启动 Worker (这一步很关键，原代码没写 start，如果是 QThread 需要 start)
            # 如果 download_manager 里已经 start 了，这里可以省略，但通常建议由调用者 start
            if hasattr(worker, 'start'):
                worker.start()

            return worker
    
    def on_download_progress(self, progress, total, speed_or_status):
            """
            下载进度更新 - 虚拟进度 + 速度显示
            Args:
                speed_or_status: 现在这个参数接收的是速度字符串 (如 "5.2MiB/s")
            """
            # 1. 安全检查
            if not (hasattr(self, 'progress_dialog') and self.progress_dialog and self.progress_dialog.isVisible()):
                return
            if self.download_state["is_closing"]:
                return

            # 获取状态
            raw_progress = float(progress)
            current_pass = self.download_state["pass"]
            last_raw = self.download_state["last_raw_progress"]
            dtype = self.download_state["type"]

            # === 检测是否进入第二阶段 (音频) ===
            if dtype == "video" and current_pass == 1 and last_raw > 80 and raw_progress < 20:
                self.download_state["pass"] = 2
                current_pass = 2

            self.download_state["last_raw_progress"] = raw_progress

            # === 计算虚拟进度 & 确定动作前缀 ===
            display_progress = 0
            action_text = ""

            if dtype == "audio":
                # 纯音频模式
                display_progress = raw_progress
                action_text = "🎵 下载音频"
            
            else: # 视频模式
                if current_pass == 1:
                    # 视频阶段 (0-95%)
                    display_progress = raw_progress * 0.95
                    action_text = "🎬 下载视频"
                elif current_pass == 2:
                    # 音频阶段 (95-99%)
                    display_progress = 95 + (raw_progress * 0.04)
                    action_text = "🎵 下载音频"

            # === 核心修改：构建显示文本 ===
            # 我们不再显示百分比，而是显示：动作 | 速度
            
            # 1. 判断传入的是不是速度 (通常包含 "/s" 或 "MiB")
            # 因为 yt-dlp 在合并时可能会发 "分段下载完成" 这种非速度文本
            is_speed_text = "s" in str(speed_or_status).lower() or "bit" in str(speed_or_status).lower()
            
            if is_speed_text:
                # 格式：🎬 下载画面 | 🚀 5.2MiB/s
                # 使用 monospaced 字体或者 emoji 让它看起来更极客
                status_text = f"{action_text} · 🚀 {speed_or_status}"
            else:
                # 如果是其他状态信息（如“计算中...”、“分段完成”），直接显示
                status_text = f"{action_text} · {speed_or_status}"

            # === 特殊处理：合并阶段 ===
            # 当虚拟进度极其接近 100% 时，说明在进行 IO 操作（合并/写入）
            if display_progress > 99:
                status_text = "🔨 正在合并音视频..."
                # 确保合并时进度条不回退，且不显示 100%（留给 finish 处理）
                display_progress = 99 

            # 更新 UI
            self.progress_dialog.update_progress(display_progress, total, status_text)

    def handle_download_finished(self, result, download_type):
            """处理下载完成"""
            if self.progress_dialog:
                # 锁死 UI
                self.download_state["is_closing"] = True
                
                # === 最终定格 ===
                # 只有这里才能设为 100%，并变绿
                if hasattr(self.progress_dialog.progress_bar, 'setEmoji'):
                    self.progress_dialog.progress_bar.setEmoji("✅")
                
                self.progress_dialog.update_status_text("✅ 所有任务处理完成！", "#43e97b")
                self.progress_dialog.progress_bar.setValue(100)
                
                def delayed_close():
                    if self.progress_dialog:
                        self.progress_dialog.close()
                        self.progress_dialog = None
                    self.download_state["is_closing"] = False
                    self.on_download_finished(result, download_type)

                from PyQt6.QtCore import QTimer
                QTimer.singleShot(1500, delayed_close)
            else:
                self.on_download_finished(result, download_type)
    
    def on_download_finished(self, result, download_type):
        """下载完成 - 接收两个参数"""
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.current_download_worker = None
        
        if result:
            print(f"✅ 下载完成: {result}")
            
            # 在这里处理结果路径转换
            if download_type == "video":
                if result:  # 检查结果是否存在
                    # 现在返回的是单个视频文件路径
                    video_file = result
                    abs_video = os.path.abspath(video_file)
                    
                    # 如果需要音频文件信息，可能需要从其他地方获取
                    # 或者修改逻辑不再依赖音频文件路径
                    result = abs_video
                else:
                    self.show_error('错误', '视频下载失败，返回为空')
                    return
            else:  # audio
                if result:
                    result = os.path.abspath(result)
            
            self.handle_download_result(result, download_type)
        else:
            self.show_error('错误', '下载失败')
    
    def on_download_error(self, error_msg):
        """下载错误"""
        print(f"❌ 下载错误: {error_msg}")
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.current_download_worker = None
        self.show_error('错误', error_msg)
    
    def cancel_current_download(self):
        """取消当前下载"""
        if self.current_download_worker:
            download_manager.cancel_worker(self.current_download_worker)
            self.current_download_worker = None
        
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        print("⏹️ 下载已取消")
        
    def normalize_video_url(self, url):
        """标准化视频URL"""
        if not url:
            return url
        
        import urllib.parse
        # 最高优先级：确保URL有协议头
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            print(f"🔗 自动添加HTTPS协议: {url}")
        
        try:
            parsed = urllib.parse.urlparse(url)
            
            # YouTube URL标准化
            if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
                # 确保使用www.youtube.com
                if parsed.netloc == 'youtube.com':
                    parsed = parsed._replace(netloc='www.youtube.com')
                elif parsed.netloc == 'm.youtube.com':
                    parsed = parsed._replace(netloc='www.youtube.com')
                elif parsed.netloc == 'youtu.be':
                    # 短链接转换
                    video_id = parsed.path.strip('/')
                    new_url = f'https://www.youtube.com/watch?v={video_id}'
                    url = new_url
                    parsed = urllib.parse.urlparse(url)
                
                # 处理查询参数 - 移除播放列表相关参数
                if parsed.query:
                    query_params = urllib.parse.parse_qs(parsed.query)
                    
                    # 移除播放列表参数
                    playlist_params_removed = []
                    for param in ['list', 'index', 'start_radio']:
                        if param in query_params:
                            del query_params[param]
                            playlist_params_removed.append(param)
                    
                    if playlist_params_removed:
                        print(f"🗑️ 移除YouTube播放列表参数: {', '.join(playlist_params_removed)}")
                        print(f"🔗 现在只下载单个视频: v={query_params.get('v', [''])[0]}")
                    
                    # 重建查询字符串
                    new_query = urllib.parse.urlencode(query_params, doseq=True)
                    parsed = parsed._replace(query=new_query)
                
                # 重建URL
                url = urllib.parse.urlunparse(parsed)
            
            # B站URL标准化（保持不变）
            elif 'bilibili.com' in parsed.netloc:
                if parsed.netloc != 'www.bilibili.com':
                    parsed = parsed._replace(netloc='www.bilibili.com')
                url = urllib.parse.urlunparse(parsed)
            
            return url
            
        except Exception as e:
            print(f"❌ URL标准化失败: {e}")
            return url

    def start_download(self, download_type="video"):

        """通用的下载启动函数 - 支持进度显示"""
        # 获取界面参数 - 如果用户提供了文件夹路径就使用，否则使用脚本目录

        folder_path = self.ui.lineEdit_folder.text()
        video_url = self.ui.lineEdit_url.text()
        if not video_url:
            self.show_error('错误', '请输入视频URL')
            return
        
        if not folder_path:
            # 使用脚本目录下的downloads子目录
            script_directory = os.path.dirname(os.path.abspath(__file__))
            folder_path = os.path.join(script_directory, "downloads")
            # 确保downloads目录存在
            if not os.path.exists(folder_path):
                try:
                    os.makedirs(folder_path)
                    print(f"创建默认下载目录: {folder_path}")
                except Exception as e:
                    self.show_error('错误', f'无法创建默认下载目录: {str(e)}')
                    return
            print(f"使用默认下载目录: {folder_path}")
        else:
            # 确保用户提供的路径存在
            if not os.path.exists(folder_path):
                try:
                    os.makedirs(folder_path)
                    print(f"创建下载目录: {folder_path}")
                except Exception as e:
                    self.show_error('错误', f'无法创建下载目录: {str(e)}')
                    return

        # URL标准化
        original_url = video_url
        video_url = self.normalize_video_url(video_url)

        cookie_file = self.ui.lineEdit_cookie.text()
        
        # 获取时间参数
        start_time_str = self.ui.lineEdit_start.text()
        end_time_str = self.ui.lineEdit_end.text()
        
        # 解析时间段
        time_range = None
        if start_time_str and end_time_str:
            time_range = f"{start_time_str}-{end_time_str}"
        elif start_time_str or end_time_str:
            self.show_error('错误', '请同时提供开始时间和结束时间，或都留空下载完整视频')
            return

        start_time_sec, end_time_sec = self.parse_time_range(time_range) if time_range else (None, None)
        
        # 获取清晰度选择
        resolution_choice = None
        if not self.ui.toggle_knob.isChecked():  # 手动模式
            if self.ui.comboBox_resolution.count() <= 1:
                # 异步获取格式信息
                if self.get_and_populate_formats_async(video_url, cookie_file):
                    return  # 退出，等待异步完成
                else:
                    self.show_error('错误', '无法开始格式获取')
                    return
            
            if self.ui.comboBox_resolution.currentIndex() > 0:
                resolution_choice = self.ui.comboBox_resolution.currentData()
            else:
                self.show_error('错误', '请在手动模式下选择清晰度')
                return
            
        # 初始化result变量
        result = None

        try:
            # 设置工作目录
            original_cwd = os.getcwd()
            os.chdir(folder_path)
            
            # 异步开始下载
            self.start_download_async(
                download_type=download_type,
                url=video_url,
                cookies_file=cookie_file if cookie_file else None,
                output_dir=folder_path,
                start_time=start_time_sec,
                end_time=end_time_sec,
                resolution_choice=resolution_choice
            )

            # 恢复工作目录
            os.chdir(original_cwd)
                
        except Exception as e:
            # 确保恢复工作目录，即使发生异常
            if 'original_cwd' in locals():
                os.chdir(original_cwd)
                
            self.show_error('错误', f'处理过程中发生错误: {str(e)}')
            import traceback
            traceback.print_exc()

    def get_system_proxy(self):
        """获取系统代理设置"""
        try:
            # 尝试从系统环境变量获取代理
            proxy = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')
            if proxy:
                print(f"检测到系统代理: {proxy}")
                return proxy
            
            # 或者返回 None 表示不使用代理
            return None
            
        except Exception as e:
            print(f"获取系统代理失败: {e}")
            return None

    # ========== 新增：解析 Netscape 格式 cookies ==========
    def load_cookies_from_netscape(file_path):
        cookies = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue  # 跳过注释和空行
                parts = line.strip().split("\t")
                if len(parts) == 7:
                    domain, flag, path, secure, expiry, name, value = parts
                    cookies[name] = value

        print(f"共识别到 {len(cookies)} 条 cookie")  # 在这里打印数量
        return cookies
    # ==================================================

    def parse_time_range(self, time_range):
        """
        解析时间段参数，格式为 HH:MM:SS-HH:MM:SS 或 MM:SS-MM:SS 或 SS-SS
        返回开始时间和结束时间（秒数）
        """
        if not time_range or '-' not in time_range:
            return None, None
        
        try:
            start_str, end_str = time_range.split('-')
            
            def time_to_seconds(time_str):
                """将时间字符串转换为秒数"""
                # 去除空格
                time_str = time_str.strip()
                parts = time_str.split(':')
                if len(parts) == 3:  # HH:MM:SS
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif len(parts) == 2:  # MM:SS
                    return int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 1:  # SS
                    return int(parts[0])
                else:
                    raise ValueError(f"无效的时间格式: {time_str}")
            
            start_seconds = time_to_seconds(start_str)
            end_seconds = time_to_seconds(end_str)
            
            if start_seconds >= end_seconds:
                print("警告：开始时间不能大于或等于结束时间，将忽略时间段参数")
                return None, None
                
            return start_seconds, end_seconds
            
        except ValueError as e:
            print(f"时间格式解析错误: {e}，将下载完整视频")
            return None, None

    def get_headers_by_selection(self):
        headers_selection = self.ui.comboBox_headers.currentText()
        headers = get_headers_by_selection(headers_selection)
        return headers
        
    def populate_resolution_combo(self, available_formats):
        """填充清晰度选择下拉框"""
        # 确保在UI线程中执行
        from PyQt6.QtCore import QTimer
        
        def update_combo():
            self.ui.comboBox_resolution.clear()
            
            # 添加"自动选择"选项
            self.ui.comboBox_resolution.addItem("自动选择最佳清晰度", "auto")
            
            # 如果有可用格式，添加它们
            if available_formats:
                # 按高度排序（从高到低）
                available_formats.sort(key=lambda x: x[1] or 0, reverse=True)
                
                for format_id, height, fps, ext, filesize in available_formats:
                    fps_display = f" {fps}FPS" if fps else ""
                    size_display = ""
                    
                    # 添加文件大小信息（如果可用）
                    if filesize:
                        size_mb = filesize / (1024 * 1024)
                        size_display = f" ({size_mb:.1f}MB)" if size_mb > 1 else f" ({filesize/1024:.0f}KB)"
                    
                    display_text = f"{height or '未知'}p{fps_display}{size_display} ({ext})"
                    self.ui.comboBox_resolution.addItem(display_text, format_id)
                
                print(f"✅ 已填充 {len(available_formats)} 个清晰度选项")
                
                # 选择第一个非自动选项
                if len(available_formats) > 0:
                    self.ui.comboBox_resolution.setCurrentIndex(1)  # 跳过"自动选择"
            else:
                print("❌ 没有可用的清晰度选项")
                self.ui.comboBox_resolution.addItem("无可用清晰度", "none")
        
        # 使用QTimer确保在UI线程中更新
        QTimer.singleShot(0, update_combo)

    def handle_download_result(self, result, download_type):
        """处理下载结果"""
        if result == "wait_for_selection":
            self.show_error('提示', '请从清晰度列表中选择一个选项，然后再次点击下载')
            return
            
        if download_type == "video":
            # 现在 result 是单个视频文件路径
            video_file = result
            
            # 规范化路径分隔符
            if video_file:
                video_file = os.path.normpath(video_file)
                
            print(f"调试信息 - 视频文件: {repr(video_file)}")
            print(f"调试信息 - 当前工作目录: {os.getcwd()}")
            
            # 检查文件是否存在（使用绝对路径）
            video_exists = video_file and os.path.exists(video_file)
            if not video_exists and video_file:
                # 尝试使用绝对路径
                abs_video = os.path.abspath(video_file)
                print(f"调试信息 - 视频文件绝对路径: {repr(abs_video)}, 存在: {os.path.exists(abs_video)}")
                video_exists = os.path.exists(abs_video)
                if video_exists:
                    video_file = abs_video
                    
            if video_exists:
                # 直接显示成功消息，不需要额外处理
                self.show_error('成功', f'视频下载完成！\n输出文件: {video_file}', 'success')
            else:
                self.show_error('错误', f'视频下载失败或文件不存在: {video_file}')
        else:  # audio
            audio_file = result
            if audio_file:
                audio_file = os.path.normpath(audio_file)
            if audio_file and os.path.exists(audio_file):
                self.show_error('成功', f'音频下载完成！\n输出文件: {audio_file}', 'success')
            else:
                self.show_error('错误', f'音频下载失败或文件不存在: {audio_file}')

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect

class CustomErrorDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, title="提示", message="", dialog_type="error"):
        super().__init__(parent)
        self.setWindowTitle(title)
        
        # --- 核心修改 1：直接定死窗口大小，不再调整窗口本身 ---
        self.fixed_width = 380
        self.fixed_height = 180
        self.setFixedSize(self.fixed_width, self.fixed_height)
        
        # 无边框 + 透明背景
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 动画参数
        self.animation_duration = 350 # 稍微调快一点，感官更流畅
        
        # --- UI 构建 ---
        # self.container 是我们要动画化的对象
        self.container = QtWidgets.QWidget(self)
        # 初始化时设为 0x0，位于中心，避免还没动画就显示出来了
        self.container.setGeometry(
            self.fixed_width // 2, 
            self.fixed_height // 2, 
            0, 0
        )
        
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(220, 180, 255, 0.95); /* 稍微增加不透明度 */
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
            }
        """)

        # 标题栏 (作为 container 的子控件)
        self.title_bar = QtWidgets.QWidget(self.container)
        self.title_bar.setGeometry(0, 0, self.fixed_width, 35)
        self.title_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.2);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }
        """)
        
        # 标题文字
        self.title_label = QtWidgets.QLabel(self.title_bar)
        self.title_label.setGeometry(15, 0, 300, 35)
        self.title_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                color: white;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.title_label.setText(title)
        
        # 关闭按钮
        self.close_btn = QtWidgets.QPushButton(self.title_bar)
        self.close_btn.setGeometry(350, 5, 24, 24)
        self.close_btn.setText("×")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.3);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.4);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.close_btn.clicked.connect(self.close_with_animation)
    
        # 图标设置
        if dialog_type == "success":
            icon_text = "✓"
            icon_color = "rgba(255, 255, 255, 0.9)"
        else:  # error
            icon_text = "⚠️" 
            icon_color = "rgba(241, 196, 15, 0.9)"

        # 计算居中 (保持原有逻辑)
        font_metrics = self.fontMetrics()
        icon_size = 40
        container_height = 150
        text_height = 50

        text_width = min(font_metrics.horizontalAdvance(message), 275)
        total_width = icon_size + 10 + text_width
        start_x = (self.fixed_width - total_width) // 2
        total_height = max(icon_size, text_height)
        start_y = (container_height - total_height) // 2

        # 图标
        self.error_icon = QtWidgets.QLabel(self.container)
        self.error_icon.setGeometry(start_x, start_y, icon_size, icon_size)
        self.error_icon.setStyleSheet(f"QLabel {{ background: transparent; border: none; color: {icon_color}; font-size: 32px; }}")
        self.error_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_icon.setText(icon_text)

        # 文本
        self.message_label = QtWidgets.QLabel(self.container)
        self.message_label.setGeometry(start_x + icon_size + 10, start_y, text_width, text_height)
        self.message_label.setStyleSheet("QLabel { background: transparent; border: none; color: white; font-size: 13px; font-weight: normal; }")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setText(message)
        
        # 确定按钮
        self.ok_btn = QtWidgets.QPushButton(self.container)
        self.ok_btn.setGeometry(140, 120, 100, 35)
        self.ok_btn.setText("确定")
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 180, 255, 0.7);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: rgba(230, 190, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(200, 160, 235, 0.9);
            }
        """)
        self.ok_btn.clicked.connect(self.close_with_animation)
 
        # 拖动相关
        self.dragging = False
        self.drag_position = QtCore.QPoint()

        self.setup_animations()

    # 注意：删除了 resizeEvent，因为窗口大小固定，不需要 container 跟随 resize

    def setup_animations(self):
        """
        核心修改 2：动画目标改为 self.container (内部控件)，而非 self (窗口)
        """
        # 1. 打开动画
        self.anim_open = QPropertyAnimation(self.container, b"geometry")
        self.anim_open.setDuration(self.animation_duration)
        # 使用 OutBack 会有弹跳效果，显得更灵动
        self.anim_open.setEasingCurve(QEasingCurve.Type.OutBack)
        
        # 2. 关闭动画
        self.anim_close = QPropertyAnimation(self.container, b"geometry")
        self.anim_close.setDuration(self.animation_duration)
        self.anim_close.setEasingCurve(QEasingCurve.Type.InBack)
        
        self.anim_close.finished.connect(self.close)

    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        
        # 1. 定义起点：窗口中心，大小为 0
        center_x = self.fixed_width // 2
        center_y = self.fixed_height // 2
        start_rect = QRect(center_x, center_y, 0, 0)
        
        # 2. 定义终点：填满整个窗口
        end_rect = QRect(0, 0, self.fixed_width, self.fixed_height)
        
        # 3. 设置并启动动画
        self.anim_open.setStartValue(start_rect)
        self.anim_open.setEndValue(end_rect)
        self.anim_open.start()
        
        # 反向设置关闭动画
        self.anim_close.setStartValue(end_rect)
        self.anim_close.setEndValue(start_rect)

    def close_with_animation(self):
        self.anim_close.start()

    # --- 拖动逻辑 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            # 记录鼠标在窗口内的相对位置
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            # 移动的是 self (顶级窗口)，视觉上 container 跟着动
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    start_time = time.time()
    
    # 1. 显示 Splash (加上防黑边属性)
    splash = GlassSplashWindow()
    splash.show()
    # 禁用交互，防止手贱点击导致未响应
    splash.setDisabled(True) 
    app.processEvents()
    
    # 2. 创建主窗口 (现在它是秒开的，因为重活都移走了)
    window = MainWindow()
    
    # 3. === 核心：手动驱动初始化 ===
    # 获取生成器
    initializer = window.lazy_init()
    
    # 循环执行每一步
    for progress, text in initializer:
        # 更新 Splash 进度和文字
        splash.update_progress(progress, text)
        
        # 【至关重要】强制刷新事件循环
        # 这就是解决"点击卡死/黑边"的银弹
        # 它确保在执行每一步耗时操作的间隙，Windows 都能收到"我还没死"的信号
        app.processEvents()

    # === 定义关闭流程 (带缩回动画 + 强制保险) ===
    def finish_start():
        # 1. 尝试播放缩回动画 (Zoom Out)
        # 既然启动是弹出来，结束就缩回去，视觉闭环
        if hasattr(splash, 'container'):
            # 计算终点 (中心点)
            center_x = splash.width() // 2
            center_y = splash.height() // 2
            end_rect = QRect(center_x, center_y, 0, 0)
            start_rect = splash.container.geometry()
            
            exit_anim = QPropertyAnimation(splash.container, b"geometry")
            exit_anim.setDuration(400)
            exit_anim.setEasingCurve(QEasingCurve.Type.InBack)
            exit_anim.setStartValue(start_rect)
            exit_anim.setEndValue(end_rect)
            
            def on_exit_finished():
                splash.close()
                window.show()
                
            exit_anim.finished.connect(on_exit_finished)
            
            # === 关键保险：防止动画报错导致 finished 信号丢失 ===
            # 如果 500ms 后动画还没结束（通常是因为报错卡住了），强制执行关闭
            QTimer.singleShot(500, on_exit_finished)
            
            splash.exit_anim = exit_anim
            exit_anim.start()
        else:
            # 如果没有容器，直接关闭
            splash.close()
            window.show()

    # === 你之前删掉的逻辑补回来 ===
    # 计算已用时间
    elapsed = time.time() - start_time
    min_display_time = 1.5 # 最小展示 1.5 秒
    
    if elapsed >= min_display_time:
        # 如果初始化太慢，已经够时间了，立即关闭
        finish_start()
    else:
        # 如果初始化太快，强行等到 1.5 秒再关闭
        remaining_ms = int((min_display_time - elapsed) * 1000)
        QTimer.singleShot(remaining_ms, finish_start)

    sys.exit(app.exec())