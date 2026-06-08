# -*- coding: utf-8 -*-
import os
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtCore import QTimer
from PyQt6.QtMultimedia import QSoundEffect

# 获取脚本所在的目录路径
script_directory = os.path.dirname(os.path.abspath(__file__))

# 将工作目录设置为脚本所在的目录
os.chdir(script_directory)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setFixedSize(831, 477)
        MainWindow.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        MainWindow.setUnifiedTitleAndToolBarOnMac(False)
        
        # ============ 设置窗口属性 - 毛玻璃效果 ============
        MainWindow.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        MainWindow.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        MainWindow.setStyleSheet("""
            QMainWindow {
                background-color: rgba(30, 30, 30, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
            }
        """)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setStyleSheet("""
            QWidget {
                background: transparent;
                border-radius: 8px;
            }
        """)
        
        # ============ 修正：自定义标题栏 ============
        self.title_bar = QtWidgets.QWidget(self.centralwidget)
        self.title_bar.setGeometry(QtCore.QRect(0, 0, 831, 35))
        self.title_bar.setObjectName("title_bar")
        self.title_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.75);  /* 减少透明度 */
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: 0px;  /* 左下角无圆角 */
                border-bottom-right-radius: 0px; /* 右下角无圆角 */
                border-bottom: 1px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        # 窗口标题 - 使用淡紫色主题
        self.window_title = QtWidgets.QLabel(self.title_bar)
        self.window_title.setGeometry(QtCore.QRect(15, 0, 300, 35))
        self.window_title.setObjectName("window_title")
        self.window_title.setStyleSheet("""
            QLabel {
                color: rgba(160, 100, 220, 1.0);  /* 淡紫色 */
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }
            QLabel:hover {
                color: rgba(220, 180, 255, 0.9);  /* 深紫色 - 悬停时 */
            }
        """)
        self.window_title.enterEvent = lambda e: play_hover_sound()
        
        # 最小化按钮
        self.minimize_btn = QtWidgets.QPushButton("−", self.title_bar)
        self.minimize_btn.setGeometry(QtCore.QRect(771, 6, 22, 22))  # 向左移动10px
        self.minimize_btn.setObjectName("minimize_btn")
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 193, 7, 0.9);
                color: black;
                border: none;
                border-radius: 11px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255, 213, 79, 1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 179, 0, 1);
            }
        """)
        
        # 关闭按钮
        self.close_btn = QtWidgets.QPushButton("×", self.title_bar)
        self.close_btn.setGeometry(QtCore.QRect(805, 6, 22, 22))  # 保持原位
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 0.9);
                color: white;
                border: none;
                border-radius: 11px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: rgba(239, 83, 80, 1);
            }
            QPushButton:pressed {
                background-color: rgba(198, 40, 40, 1);
            }
        """)
        
        # 添加音效和状态管理
        self.hover_sound = QSoundEffect()
        self.hover_sound.setSource(QUrl.fromLocalFile("bell.wav"))
        self.hover_sound.setVolume(0.5)
        
        # 音效状态控制
        self.sound_can_play = True
        self.sound_cooldown_timer = QTimer()
        self.sound_cooldown_timer.setSingleShot(True)
        self.sound_cooldown_timer.timeout.connect(lambda: setattr(self, 'sound_can_play', True))
        
        # 音效播放控制函数
        def play_hover_sound():
            if self.sound_can_play and self.hover_sound.isLoaded():
                self.sound_can_play = False
                self.hover_sound.play()
                # 固定冷却时间800ms（音效时长+间隔）
                self.sound_cooldown_timer.start(800)
        
        # 最小化按钮 - 添加音效
        self.minimize_btn = QtWidgets.QPushButton("−", self.title_bar)
        self.minimize_btn.setGeometry(QtCore.QRect(771, 6, 22, 22))
        self.minimize_btn.setObjectName("minimize_btn")
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 193, 7, 0.9);
                color: black;
                border: none;
                border-radius: 11px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255, 213, 79, 1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 179, 0, 1);
            }
        """)
        self.minimize_btn.enterEvent = lambda e: play_hover_sound()
        
        # 关闭按钮 - 添加音效
        self.close_btn = QtWidgets.QPushButton("×", self.title_bar)
        self.close_btn.setGeometry(QtCore.QRect(805, 6, 22, 22))
        self.close_btn.setObjectName("close_btn")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 67, 54, 0.9);
                color: white;
                border: none;
                border-radius: 11px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: rgba(239, 83, 80, 1);
            }
            QPushButton:pressed {
                background-color: rgba(198, 40, 40, 1);
            }
        """)
        self.close_btn.enterEvent = lambda e: play_hover_sound()
        
        #UI部分代码
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.lower()  # 将背景图片置于底层
        self.label.setGeometry(QtCore.QRect(0, 35, 831, 442))  # 设置label的geometry
        font = QtGui.QFont()
        font.setFamily("VIP全字符SleeK")
        self.label.setFont(font)
        self.label.setText("")
        self.label.setScaledContents(True)
        self.label.setObjectName("label")

        # ============ 创建中心布局容器 ============
        self.center_container = QtWidgets.QWidget(self.centralwidget)
        self.center_container.setGeometry(QtCore.QRect(0, 35, 831, 442))
        self.center_container.setObjectName("center_container")
        self.center_container.setStyleSheet("background: transparent;")

        # 创建主垂直布局
        self.main_layout = QtWidgets.QVBoxLayout(self.center_container)
        self.main_layout.setContentsMargins(120, 40, 120, 40)  # 减少边距，增加可用空间
        self.main_layout.setSpacing(18)  # 增加行间距

        # 第一行：视频URL输入框
        self.url_layout = QtWidgets.QHBoxLayout()
        self.url_layout.setSpacing(10)

        self.lineEdit_url = QtWidgets.QLineEdit(self.center_container)
        self.lineEdit_url.setObjectName("lineEdit_url")
        self.lineEdit_url.setPlaceholderText("请输入视频URL")
        self.lineEdit_url.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 6px;
                padding: 12px 15px;
                font-size: 14px;
                color: rgba(220, 180, 255, 0.95);
                min-height: 30px;
                font-weight: bold;
            }
            QLineEdit:focus {
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(180, 150, 255, 0.8);
            }
            QLineEdit::placeholder {
                color: rgba(220, 180, 255, 0.7);
                font-weight: normal;
            }
        """)

        self.url_layout.addWidget(self.lineEdit_url)

        # 第二行：Cookie文件选择
        self.cookie_layout = QtWidgets.QHBoxLayout()
        self.cookie_layout.setSpacing(10)

        self.lineEdit_cookie = QtWidgets.QLineEdit(self.center_container)
        self.lineEdit_cookie.setObjectName("lineEdit_cookie")
        self.lineEdit_cookie.setPlaceholderText("Cookie文件路径（可选）")
        self.lineEdit_cookie.setStyleSheet(self.lineEdit_url.styleSheet())

        self.pushButton_select_cookie = QtWidgets.QPushButton(self.center_container)
        font = QtGui.QFont()
        font.setFamily("VIP全字符SleeK")
        self.pushButton_select_cookie.setFont(font)
        self.pushButton_select_cookie.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        self.pushButton_select_cookie.setObjectName("pushButton_select_cookie")
        self.pushButton_select_cookie.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 180, 255, 0.7);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: rgba(230, 190, 255, 0.9);
            }
            QPushButton:pressed {
                background-color: rgba(200, 160, 235, 0.9);
            }
        """)

        self.cookie_layout.addWidget(self.lineEdit_cookie)
        self.cookie_layout.addWidget(self.pushButton_select_cookie)
        self.cookie_layout.setStretch(0, 3)
        self.cookie_layout.setStretch(1, 1)

        # 第三行：保存文件夹选择
        self.folder_layout = QtWidgets.QHBoxLayout()
        self.folder_layout.setSpacing(10)

        self.lineEdit_folder = QtWidgets.QLineEdit(self.center_container)
        self.lineEdit_folder.setObjectName("lineEdit_folder")
        self.lineEdit_folder.setPlaceholderText("视频保存文件夹")
        self.lineEdit_folder.setStyleSheet(self.lineEdit_url.styleSheet())

        self.pushButton_select_folder = QtWidgets.QPushButton(self.center_container)
        self.pushButton_select_folder.setObjectName("pushButton_select_folder")
        self.pushButton_select_folder.setStyleSheet(self.pushButton_select_cookie.styleSheet())

        self.folder_layout.addWidget(self.lineEdit_folder)
        self.folder_layout.addWidget(self.pushButton_select_folder)
        self.folder_layout.setStretch(0, 3)
        self.folder_layout.setStretch(1, 1)

        # 第四行：时间范围选择
        self.time_layout = QtWidgets.QHBoxLayout()
        self.time_layout.setSpacing(10)

        self.lineEdit_start = QtWidgets.QLineEdit(self.center_container)
        self.lineEdit_start.setObjectName("lineEdit_start")
        self.lineEdit_start.setPlaceholderText("开始时间 (MM:SS 或 秒数)")
        self.lineEdit_start.setStyleSheet(self.lineEdit_url.styleSheet())

        self.lineEdit_end = QtWidgets.QLineEdit(self.center_container)
        self.lineEdit_end.setObjectName("lineEdit_end")
        self.lineEdit_end.setPlaceholderText("结束时间 (MM:SS 或 秒数)")
        self.lineEdit_end.setStyleSheet(self.lineEdit_url.styleSheet())

        self.time_layout.addWidget(self.lineEdit_start)
        self.time_layout.addWidget(self.lineEdit_end)

        # 第五行：Headers选择和清晰度选择
        self.headers_layout = QtWidgets.QHBoxLayout()
        self.headers_layout.setSpacing(10)

        # ComboBox通用样式 - 淡紫色背景
        combo_style = """
            QComboBox {
                background-color: rgba(255, 255, 255, 0.25);
                color: rgba(220, 180, 255, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QComboBox:hover {
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.6);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid rgba(220, 180, 255, 0.9);
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(220, 180, 255, 0.8);
                color: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.4);
                outline: 0px;
                padding: 8px;
                font-weight: bold;
                border-radius: 0px;
            }
            QComboBox QAbstractItemView::item {
                background-color: transparent;
                padding: 12px 15px;
                margin: 2px 0px;
                border: none;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: rgba(74, 144, 226, 0.8);
                color: white;
                border: none;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: rgba(74, 144, 226, 0.6);
                border: none;
            }
            QComboBox:disabled {
                background-color: rgba(255, 255, 255, 0.15);
                color: rgba(220, 180, 255, 0.6);
            }
        """

        # Headers ComboBox
        self.comboBox_headers = QtWidgets.QComboBox(self.center_container)
        self.comboBox_headers.setObjectName("comboBox_headers")
        self.comboBox_headers.addItem("PC")
        self.comboBox_headers.addItem("Mobile")
        self.comboBox_headers.addItem("iOS")
        self.comboBox_headers.setStyleSheet(combo_style)

        # 清晰度 ComboBox
        self.comboBox_resolution = QtWidgets.QComboBox(self.center_container)
        self.comboBox_resolution.setObjectName("comboBox_resolution")
        self.comboBox_resolution.addItem("自动选择最佳清晰度")
        self.comboBox_resolution.setStyleSheet(combo_style)

        self.headers_layout.addWidget(self.comboBox_headers)
        self.headers_layout.addWidget(self.comboBox_resolution)
        self.headers_layout.setStretch(0, 1)
        self.headers_layout.setStretch(1, 1)

        # 第六行：下载视频和下载音频按钮
        self.download_layout = QtWidgets.QHBoxLayout()
        self.download_layout.setSpacing(15)  # 增加按钮间距

        # 下载视频按钮
        self.pushButton_download_video = QtWidgets.QPushButton(self.center_container)
        self.pushButton_download_video.setObjectName("pushButton_download_video")
        self.pushButton_download_video.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 180, 255, 0.7);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 6px 20px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
                min-height: 32px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: rgba(230, 190, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(200, 160, 235, 0.9);
            }
        """)

        # 下载音频按钮
        self.pushButton_download_audio = QtWidgets.QPushButton(self.center_container)
        self.pushButton_download_audio.setObjectName("pushButton_download_audio")
        self.pushButton_download_audio.setStyleSheet(self.pushButton_download_video.styleSheet())

        # 将下载按钮居中
        self.download_layout.addStretch(1)
        self.download_layout.addWidget(self.pushButton_download_video)
        self.download_layout.addWidget(self.pushButton_download_audio)
        self.download_layout.addStretch(1)

        # 将各行布局添加到主布局
        self.main_layout.addLayout(self.url_layout)
        self.main_layout.addLayout(self.cookie_layout)
        self.main_layout.addLayout(self.folder_layout)
        self.main_layout.addLayout(self.time_layout)
        self.main_layout.addLayout(self.headers_layout)
        self.main_layout.addLayout(self.download_layout)

        # 添加弹性空间使内容垂直居中
        self.main_layout.insertStretch(0)  # 顶部弹性空间
        self.main_layout.addStretch(1)     # 底部弹性空间

        # 设置下载按钮高度
        self.pushButton_download_video.setMinimumHeight(35)
        self.pushButton_download_audio.setMinimumHeight(35)

        # 使用QPushButton和QLabel组合实现拨片开关
        self.toggle_container = QtWidgets.QWidget(self.centralwidget)
        self.toggle_container.setGeometry(QtCore.QRect(20, 420, 50, 50))  # 进一步下移，增加高度
        self.toggle_container.setStyleSheet("background: transparent;")

        # 开关轨道 - 缩短轨道长度并确保不与圆形重叠
        self.toggle_track = QtWidgets.QLabel(self.toggle_container)
        self.toggle_track.setGeometry(QtCore.QRect(15, 15, 20, 4))  # 调整轨道位置
        self.toggle_track.setStyleSheet("""
            background-color: rgba(220, 180, 255, 0.7);
            border-radius: 2px;
        """)

        # 开关圆形
        self.toggle_knob = QtWidgets.QPushButton(self.toggle_container)
        self.toggle_knob.setGeometry(QtCore.QRect(30, 7, 20, 20))  # 调整初始位置
        self.toggle_knob.setCheckable(True)
        self.toggle_knob.setChecked(True)
        self.toggle_knob.setStyleSheet("""
            QPushButton {
                background-color: rgba(220, 180, 255, 0.9);
                border: none;
                border-radius: 10px;
            }
            QPushButton:checked {
                background-color: rgba(220, 180, 255, 0.9);
                border: none;
            }
            QPushButton:unchecked {
                background-color: transparent;
                border: 2px solid rgba(220, 180, 255, 0.7);
                border-radius: 10px;
            }
        """)

        # 添加状态标签 - 放在按钮下方，调整位置以更好对齐
        self.toggle_label = QtWidgets.QLabel(self.toggle_container)
        self.toggle_label.setGeometry(QtCore.QRect(0, 32, 50, 15))  # 调整位置和高度
        self.toggle_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.toggle_label.setStyleSheet("""
            color: rgba(220, 180, 255, 0.9); 
            font-size: 11px; 
            font-weight: bold;
            background: transparent;
        """)
        self.toggle_label.setText("自动选择")

        # 连接信号 - 先定义方法再连接
        def toggle_resolution_combo(checked):
            """切换清晰度选择框的启用状态"""
            self.comboBox_resolution.setEnabled(not checked)
            update_toggle_position(checked)

        def update_toggle_position(checked):
            """更新开关圆形的位置和样式"""
            if checked:
                # 打开状态 - 圆形滑到最右侧，轨道实心
                self.toggle_knob.setGeometry(QtCore.QRect(30, 7, 20, 20))  # 最右侧
                self.toggle_knob.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(220, 180, 255, 0.9);
                        border: none;
                        border-radius: 10px;
                    }
                """)
                self.toggle_track.setStyleSheet("""
                    background-color: rgba(220, 180, 255, 0.7);
                    border-radius: 2px;
                """)
                self.toggle_label.setText("自动选择")
            else:
                # 关闭状态 - 圆形滑到最左侧，轨道空心
                self.toggle_knob.setGeometry(QtCore.QRect(0, 7, 20, 20))   # 最左侧
                self.toggle_knob.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: 2px solid rgba(220, 180, 255, 0.7);
                        border-radius: 10px;
                    }
                """)
                self.toggle_track.setStyleSheet("""
                    background-color: transparent;
                    border: 1px solid rgba(220, 180, 255, 0.7);
                    border-radius: 2px;
                """)
                self.toggle_label.setText("手动选择")

        # 现在连接信号
        self.toggle_knob.toggled.connect(toggle_resolution_combo)

        # 初始化开关位置和样式
        update_toggle_position(True)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        # 设置壁纸
        self.label.setPixmap(QtGui.QPixmap("723.webp"))

        # ============ 连接按钮信号 ============
        self.close_btn.clicked.connect(MainWindow.close)
        self.minimize_btn.clicked.connect(MainWindow.showMinimized)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        # 设置自定义标题栏的文本
        self.window_title.setText(_translate("MainWindow", "视频下载工具 v1.2测试版"))
        self.pushButton_download_video.setText(_translate("MainWindow", "下载视频"))
        self.pushButton_download_audio.setText(_translate("MainWindow", "下载音频"))
        self.pushButton_select_cookie.setText(_translate("MainWindow", "选择Cookie"))
        self.pushButton_select_folder.setText(_translate("MainWindow", "选择文件夹"))
        self.comboBox_resolution.setItemText(0, _translate("MainWindow", "自动选择最佳清晰度"))
        self.comboBox_headers.setItemText(0, _translate("MainWindow", "PC"))
        self.comboBox_headers.setItemText(1, _translate("MainWindow", "Mobile"))
        self.comboBox_headers.setItemText(2, _translate("MainWindow", "iOS"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())



