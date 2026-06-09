# Ytp-Dlp-GUI
<img width="256" height="256" alt="ak3mh-4ls6r" src="https://github.com/user-attachments/assets/e9beec77-9453-4dfb-abd8-7261c99e3602" /><br>

<img width="1455" height="829" alt="捕获" src="https://github.com/user-attachments/assets/ce77cbe1-6d6b-4166-9336-b49c708fc3f7" /><br>

一个基于Ytp-dlp和QT6开发的简易GUI客户端

由于我没有时间维护此项目，所以选择开源，包括完整的客户端文件

其中的部分代码可能已经过时，但主要功能依然正常工作

经测试，6月9号，通过手动注入Cookie，依然可以正常下载B站视频，而油管可以通过调用QJS，在无需Cookie的情况下下载视频

针对这两个平台做过少量适配，其它平台则依赖Ytp-Dlp自身的调用（可能会有报错）

欢迎感兴趣的佬接手该项目（或者提交代码），你也可用通过nuitka将其编译成直接可用的客户端

## 依赖
- Python 3.8+
- FFmpeg（视频合并需要）
- yt-dlp

## 安装

```bash
# 克隆仓库
git clone https://github.com/lite-fish/Ytp-Dlp-GUI.git
cd Ytp-Dlp-GUI

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行
python 2.py

## 许可证
AGPL-3.0 license

