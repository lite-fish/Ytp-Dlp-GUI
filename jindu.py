from PyQt6.QtWidgets import QDialog, QProgressBar, QLabel, QVBoxLayout, QMessageBox, QApplication, QSizePolicy
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PyQt6.QtGui import QFont, QPalette, QColor
import time
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*PyQt6.*")

# 假设这是你的自定义进度条类

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFrame, 
                             QGraphicsDropShadowEffect, QSizePolicy)
from PyQt6.QtCore import Qt, QPoint

class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("视频下载进度")
        
        # 1. 关键修改：只限制宽度和最小高度，绝不限制最大高度！
        # 这样拖动时 Qt 就不会因为计算误差报错了
        self.setFixedWidth(470)      # 固定宽度 (含阴影区)
        self.setMinimumHeight(200)   # 最小高度 (含阴影区)

        # 无边框 + 透明背景
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.m_flag = False
        self.m_Position = QPoint()

        self.create_ui()

    def create_ui(self):
        # 外部布局：留出阴影空间
        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(10, 10, 10, 10) 
        
        # 背景容器
        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainFrame")
        self.main_container.setStyleSheet("""
            QFrame#MainFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50, stop:0.5 #34495e, stop:1 #3498db);
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,0.2);
            }
        """)
        
        # 阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 0)
        self.main_container.setGraphicsEffect(shadow)
        
        window_layout.addWidget(self.main_container)

        # 内部布局
        self.container_layout = QVBoxLayout(self.main_container)
        # 增加底部边距，防止文字太长时贴底
        self.container_layout.setContentsMargins(25, 20, 25, 25) 
        self.container_layout.setSpacing(15)

        # 1. 标题
        title_label = QLabel("🎯 视频下载进度")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white; font-size: 18px; font-weight: bold;
                background: rgba(255,255,255,0.1); border-radius: 10px; padding: 5px;
            }
        """)
        title_label.setFixedHeight(40)
        
        # 2. 进度条
        self.progress_bar = RoundedProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(30) 

        # 3. 状态标签 (关键设置)
        self.status_label = QLabel("正在初始化...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 设置 SizePolicy：垂直方向 Preferrred (根据内容决定)，水平方向 Expanding
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        # 开启自动换行
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(40) # 最小留出两行的高度
        
        self.container_layout.addWidget(title_label)
        self.container_layout.addWidget(self.progress_bar)
        self.container_layout.addWidget(self.status_label)

        self.update_status_text("正在初始化下载进程...", "rgba(255,255,255,0.9)")
        
        # 添加一个弹性空间，当文字很少时，让内容靠上一点，或者保持居中
        # self.container_layout.addStretch() 

    # === 拖拽逻辑 (保持稳健) ===
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.m_flag = True
            self.m_Position = event.globalPosition().toPoint() - self.pos()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if Qt.MouseButton.LeftButton and self.m_flag:
            self.move(event.globalPosition().toPoint() - self.m_Position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        self.m_flag = False

    # === 更新逻辑 ===
    def update_progress(self, progress, total, status):
        """
        更新 UI
        【修复点 2】: 删除了自动变绿勾的逻辑。
        现在不管是不是 100%，这里都只显示普通的白色/蓝色，
        把“变绿”的权力完全交给主程序。
        """
        self.progress_bar.setValue(int(progress))
        
        # 始终保持普通颜色，除非主程序显式传入了完成状态的颜色
        # 我们这里统一用白色，具体的“成功绿色”在 update_status_text 里由参数控制
        # 或者简单点，普通状态就是白色
        color = "rgba(255,255,255,0.95)"
            
        self.update_status_text(status, color)

    def update_status_text(self, text, color):
        """
        更新文本并自动调整窗口高度
        """
        base_style = f"""
            QLabel {{
                color: {color};
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
                padding: 8px; /* 增加内边距让多行文字更好看 */
                qproperty-alignment: AlignCenter;
            }}
        """

        # 根据文字长度决定字体大小，但始终允许换行
        # 这里只是简单判断一下，如果特别长就稍微改小一点点字体，避免太突兀
        if len(text) > 50:
             self.status_label.setStyleSheet(base_style + "QLabel { font-size: 11px; font-weight: normal; }")
        else:
             self.status_label.setStyleSheet(base_style + "QLabel { font-size: 13px; font-weight: normal; }")
        
        self.status_label.setText(text)
            
        # === 核心逻辑：通知窗口调整大小 ===
        # adjustSize() 会让窗口根据 Layout 的 sizeHint 重新计算尺寸
        # 如果文字变多 -> Label 变高 -> Container 变高 -> Window 变高
        self.adjustSize()

    def create_progress_messagebox(parent=None):
        """创建带进度条的现代化QMessageBox"""
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle("下载进度")
        msg_box.setWindowOpacity(0.8)  # 80% 不透明度
        
        # 设置现代化样式
        msg_box.setStyleSheet("""
            QMessageBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3c72, stop:1 #2a5298);
                border-radius: 12px;
                border: 2px solid #4a90e2;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        msg_box.setText("🔐 正在下载文件...")
        
        # 使用自定义进度条替换原来的QProgressBar
        progress_bar = RoundedProgressBar()
        progress_bar.setValue(0)
        
        # 创建状态标签
        status_label = QLabel("准备开始...")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        # 添加到消息框
        layout = msg_box.layout()
        layout.addWidget(status_label, 1, 0)
        layout.addWidget(progress_bar, 2, 0)
        
        # 存储进度条和标签的引用
        msg_box.progress_bar = progress_bar
        msg_box.status_label = status_label
        
        # 移除标准按钮
        msg_box.setStandardButtons(QMessageBox.StandardButton.NoButton)
        
        return msg_box

from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QObject

class DownloadWorker(QThread):
    """
    后台下载工作线程
    负责执行耗时的下载任务，不卡死界面
    """
    progress_signal = pyqtSignal(int, int, str) # 进度信号
    finished_signal = pyqtSignal(object)        # 完成信号(带结果)
    error_signal = pyqtSignal(Exception)        # 错误信号

    def __init__(self, main_window, download_type, *args):
        super().__init__()
        self.main_window = main_window
        self.download_type = download_type
        self.args = args

    def run(self):
        try:
            # 定义一个内部回调，把 main_window 的进度转成信号发出去
            def internal_callback(progress, total, status):
                self.progress_signal.emit(int(progress), int(total), str(status))

            # 根据类型调用不同的下载方法
            # 注意：这里我们把 args 解包传进去，并把 callback 替换成我们的 internal_callback
            url, cookies, out_dir, start, end, res = self.args
            
            if self.download_type == "video":
                result = self.main_window.download_video(
                    url, cookies, out_dir, start, end, res, internal_callback
                )
            else:
                result = self.main_window.download_audio(
                    url, cookies, out_dir, start, end, res, internal_callback
                )
            
            self.finished_signal.emit(result)
            
        except Exception as e:
            self.error_signal.emit(e)

def download_with_progress_dig(main_window_instance, download_type, url, cookies_file, 
                             output_dir='downloads', start_time=None, end_time=None, 
                             resolution_choice=None, 
                             success_callback=None, # 新增：成功后的回调函数
                             error_callback=None):  # 新增：失败后的回调函数
    """
    重构后的下载函数：异步执行，UI丝滑
    注意：此函数不再直接 return result，而是通过 success_callback 返回结果
    """
    
    # 1. 创建进度窗口 (使用之前优化过的版本)
    progress_dialog = ProgressDialog(main_window_instance)
    progress_dialog.show() # 窗口会自动且流畅地显示，不需要 processEvents
    
    # 2. 状态标志位
    state = {
        "is_download_done": False, # 下载是否完成
        "is_min_time_up": False,   # 最小展示时间是否到了
        "download_result": None,   # 暂存下载结果
        "download_error": None     # 暂存错误信息
    }

    # 3. 创建工作线程
    worker = DownloadWorker(
        main_window_instance, 
        download_type, 
        url, cookies_file, output_dir, start_time, end_time, resolution_choice
    )

    # 4. 定义检查关闭逻辑 (当下载完成 且 最小时间到了，才关闭)
    def check_and_close():
        if state["is_download_done"] and state["is_min_time_up"]:
            progress_dialog.close()
            # 触发外部回调
            if state["download_error"]:
                if error_callback: error_callback(state["download_error"])
            elif state["download_result"]:
                if success_callback: success_callback(state["download_result"])

    # 5. 设置最小显示时间计时器 (3秒)
    def on_min_time_reached():
        state["is_min_time_up"] = True
        # 如果下载太快，时间到了就直接把进度条拉满
        if state["is_download_done"]:
            progress_dialog.update_progress(100, 100, "✅ 处理完成")
            # 稍微停顿一下让用户看到100%，体验更好
            QTimer.singleShot(500, check_and_close)
        else:
            check_and_close()

    QTimer.singleShot(3000, on_min_time_reached) # 3秒后触发

    # 6. 连接线程信号
    def on_worker_progress(curr, total, status):
        progress_dialog.update_progress(curr, total, status)

    def on_worker_finished(result):
        state["is_download_done"] = True
        state["download_result"] = result
        progress_dialog.update_progress(100, 100, "✅ 下载完成，正在整理...")
        check_and_close()

    def on_worker_error(err):
        state["is_download_done"] = True
        state["download_error"] = err
        progress_dialog.update_progress(100, 100, "❌ 下载出错")
        check_and_close()

    worker.progress_signal.connect(on_worker_progress)
    worker.finished_signal.connect(on_worker_finished)
    worker.error_signal.connect(on_worker_error)

    # 7. 启动线程
    # 为了防止垃圾回收机制把 worker 销毁，我们把它挂载到 dialog 上
    progress_dialog._worker = worker 
    worker.start()
    
from PyQt6.QtWidgets import QFrame, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty

class RoundedProgressBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self.setup_ui()
    
    def setup_ui(self):
        self.setMinimumHeight(30)
        # 1. 设置主样式：背景透明度很重要，防止直角底色透出来
        self.setStyleSheet("""
            RoundedProgressBar {
                background: rgba(255,255,255,0.1); 
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 15px;
            }
        """)
        
        # 2. 进度填充层
        self.progress_fill = QFrame(self)
        self.progress_fill.setFixedHeight(26)
        
        # === 关键修复：初始化时强行把宽度设为 0 ===
        # 防止布局还没算好时，它以默认大小显示出来，导致“溢出”
        self.progress_fill.resize(0, 26)
        self.progress_fill.move(2, 2) # 初始位置也定好
        
        self.progress_fill.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #43e97b, stop:0.5 #38f9d7, stop:1 #4facfe);
                border-radius: 13px;
            }
        """)
        
        # 3. 文本标签
        self.text_label = QLabel("⏳ 0%", self)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        
        # === 关键修复：初始化完立马刷新一次 ===
        self.setValue(0)
    
    def setValue(self, value):
        self._value = max(0, min(100, int(value)))
        self.text_label.setText(f"⏳ {self._value}%")
        
        # 立即计算宽度
        self._update_fill_width()
    
    def setEmoji(self, emoji):
        self.text_label.setText(f"{emoji} {self._value}%")

    def _update_fill_width(self):
        """计算并设置填充条宽度"""
        # 获取当前控件的实际宽度
        current_width = self.width()
        
        # === 关键修复：如果宽度无效（还没显示），直接设为0并返回 ===
        # 避免在窗口初始化阶段计算出错误的坐标
        if current_width <= 10: 
            self.progress_fill.setFixedWidth(0)
            return

        available_width = current_width - 4
        target_width = int(available_width * self._value / 100)
        
        # 垂直居中计算
        y_pos = (self.height() - self.progress_fill.height()) // 2
        
        # 设置几何形状
        self.progress_fill.setGeometry(2, y_pos, max(0, target_width), 26)

    def resizeEvent(self, event):
        """窗口大小改变时触发"""
        super().resizeEvent(event)
        # 确保标签覆盖全域
        self.text_label.setGeometry(0, 0, self.width(), self.height())
        # 重新计算进度条
        self._update_fill_width()
    
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QEventLoop # 引入 QEventLoop

def test_progress_dialog():
    """测试进度对话框（非阻塞版）"""
    app = QApplication([])
    
    # 创建进度对话框
    dialog = ProgressDialog()
    dialog.show()

    # --- 核心修改：定义一个非阻塞的等待函数 ---
    def wait(milliseconds):
        """
        这个函数代替 time.sleep
        它会让出主线程控制权，允许界面刷新、拖动、响应鼠标，
        直到时间结束。
        """
        loop = QEventLoop()
        QTimer.singleShot(milliseconds, loop.quit)
        loop.exec() 

    # 模拟进度更新逻辑
    def simulate_progress():
        # 1. 测试短文字
        dialog.update_progress(0, 100, "正在初始化下载进程...")
        wait(1000) # 等待1秒，期间窗口可拖动，无黑边
        
        # 2. 测试中等长度文字
        dialog.update_progress(25, 100, "正在下载文件：这是一个中等长度的文件名.mp4")
        wait(1000)
        
        # 3. 测试长文字
        long_text = "正在下载文件：这是一个非常长的文件名用来测试标签滚动效果_高清视频教程_2024年最新版本_包含所有章节内容.mp4"
        dialog.update_progress(50, 100, long_text)
        wait(2000)
        
        # 4. 测试超长文字
        very_long_text = "正在处理：这是一个超长的状态信息用来测试标签的滚动显示效果，当文字内容超过标签宽度时应该能够自动滚动显示完整内容，这是一个非常重要的功能测试.mp4"
        dialog.update_progress(75, 100, very_long_text)
        wait(2000)
        
        # 5. 完成
        dialog.update_progress(100, 100, "下载完成！")
        wait(1000)
        
        # 关闭应用
        dialog.close()
        # 注意：这里不需要 quit，因为 exec 会在下面运行，关闭窗口通常结束循环
        # 如果需要彻底退出测试脚本：
        app.quit()
    
    # 延迟 100ms 后启动模拟，给窗口一点初始化的时间
    QTimer.singleShot(100, simulate_progress)
    
    app.exec()

if __name__ == "__main__":
    test_progress_dialog()