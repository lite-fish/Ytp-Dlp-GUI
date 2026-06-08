# async_downloader.py
import os
import re
import sys
import multiprocessing
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PyQt6.QtCore import QRunnable, QThreadPool, pyqtSignal, QObject, QTimer
import yt_dlp

def get_base_path():
    """获取程序根目录，兼容开发和打包环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return sys._MEIPASS
    # 开发时的脚本所在目录
    return os.path.dirname(os.path.abspath(__file__))

qjs_exe_path = os.path.join(get_base_path(), 'qjs.exe') 

class DownloadSignals(QObject):
    """下载信号基类"""
    started = pyqtSignal()
    progress = pyqtSignal(int, int, str)  # 当前进度, 总进度, 状态
    finished = pyqtSignal(object)  # 结果
    error = pyqtSignal(str)  # 错误信息

class FormatFetchSignals(DownloadSignals):
    """格式获取专用信号"""
    formats_ready = pyqtSignal(list)  # 格式列表

class FormatFetchWorker(QRunnable):
    """格式获取工作器"""
    
    def __init__(self, url, cookies_file=None):
        super().__init__()
        self.url = url
        self.cookies_file = cookies_file
        self.signals = FormatFetchSignals()
        self.setAutoDelete(True)
    
    def run(self):
        """在工作线程中执行格式获取"""
        try:
            self.signals.started.emit()
            self.signals.progress.emit(0, 100, "正在获取格式信息...")
            
            ydl_opts = {
                'listformats': True,
                'simulate': True,
                'quiet': True,
            }
            
            if self.cookies_file:
                ydl_opts['cookiefile'] = self.cookies_file
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.url, download=False)
                formats = info_dict.get('formats', [])
                
                # 获取可用的视频格式
                available_formats = []
                for f in formats:
                    if f.get('vcodec') != 'none':  # 只包含视频格式
                        format_id = f.get('format_id', '')
                        height = f.get('height', 0)
                        fps = f.get('fps', 0)
                        ext = f.get('ext', '')
                        filesize = f.get('filesize', f.get('filesize_approx', 0))
                        available_formats.append((format_id, height, fps, ext, filesize))
                
                self.signals.progress.emit(100, 100, "格式获取完成")
                self.signals.formats_ready.emit(available_formats)
                self.signals.finished.emit(available_formats)
                
        except Exception as e:
            error_msg = f"获取格式信息失败: {e}"
            self.signals.error.emit(error_msg)
            self.signals.finished.emit(None)

class DownloadWorker(QRunnable):
    """下载工作器基类"""
    
    def __init__(self, url, cookies_file=None, output_dir='downloads', 
                 start_time=None, end_time=None, resolution_choice=None):
        super().__init__()
        self.url = url
        self.cookies_file = cookies_file
        self.output_dir = output_dir
        self.start_time = start_time
        self.end_time = end_time
        self.resolution_choice = resolution_choice
        self.signals = DownloadSignals()
        self.setAutoDelete(True)
        
        # 进度跟踪
        self.last_progress = 0
        self.progress_pattern = re.compile(r'(\d+\.\d+)%')

class VideoDownloadWorker(DownloadWorker):
    """视频下载工作器"""
    
    def __init__(self, url, cookies_file=None, output_dir='downloads', 
                 start_time=None, end_time=None, resolution_choice=None,
                 system_proxy=None, headers=None):
        super().__init__(url, cookies_file, output_dir, start_time, end_time, resolution_choice)
        self.system_proxy = system_proxy
        self.headers = headers
    
    def run(self):
        """在工作线程中执行视频下载"""
        try:
            self.signals.started.emit()
            self.signals.progress.emit(0, 100, "准备下载视频...")
            
            result = self._download_video()
            self.signals.finished.emit(result)
            
        except Exception as e:
            error_msg = f"视频下载失败: {e}"
            import traceback
            traceback.print_exc()
            self.signals.error.emit(error_msg)
            self.signals.finished.emit(None)
    
    def _download_video(self):
        """实际的视频下载逻辑 - 集成 curl_cffi 浏览器指纹模拟"""
        try:
            # 检查当前目录是否已经是downloads目录
            current_dir = os.getcwd()
            current_dir_name = os.path.basename(current_dir)
            
            # 如果当前目录已经是downloads，就直接使用当前目录
            if current_dir_name.lower() == 'downloads' or self.output_dir in current_dir:
                self.output_dir = current_dir  # 直接使用当前目录
                print(f"使用当前目录作为输出目录: {self.output_dir}")
            else:
                # 否则创建/使用指定的输出目录
                if not os.path.exists(self.output_dir):
                    os.makedirs(self.output_dir)
                    print(f"创建输出目录: {self.output_dir}")
                else:
                    print(f"使用现有输出目录: {self.output_dir}")
            
            # 第二步：配置 yt-dlp 使用浏览器指纹数据
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'noprogress': True,
                'noplaylist': True,
                'quiet': False,
                'progress_hooks': [self._create_progress_hook()],
                # 网络优化设置
                'retries': 15,
                'fragment_retries': 15,
                'skip_unavailable_fragments': True,
                'retry_sleep_functions': {
                    'http': lambda n: 8,
                    'ftp': lambda n: 8,
                    'file': lambda n: 3,
                },
                'buffersize': 1024 * 1024 * 2,  # 增大缓冲区
                'http_chunk_size': 15 * 1024 * 1024,  # 增大分块大小
                'continuedl': True,
                'no_part': False,
                'js_runtimes': {
                    'quickjs': {
                        'args': [qjs_exe_path],
                    },
                },
            }

            # 添加代理、cookies和headers
            if self.system_proxy:
                ydl_opts['proxy'] = self.system_proxy
            if self.cookies_file:
                ydl_opts['cookiefile'] = self.cookies_file
                cookies_file = self.cookies_file
            if self.headers:
                ydl_opts['http_headers'] = self.headers
            
            # 先获取视频信息来生成 base_filename
            print("📡 获取视频信息...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.url, download=False)
            
            # 生成 base_filename
            base_filename = re.sub(r'[^\w\-_\. ]', '_', info_dict['title'])
            print(f"生成基础文件名: {base_filename}")
            
            print("🎬 开始下载视频...")
            self.signals.progress.emit(0, 100, "准备下载视频...")

            # 更新 yt-dlp 选项，添加文件名
            ydl_opts['outtmpl'] = os.path.join(self.output_dir, f'{base_filename}.%(ext)s')
            
            # 添加时间段参数
            if self.start_time is not None and self.end_time is not None:
                ydl_opts['download_ranges'] = lambda info_dict, ydl: [
                    {'start_time': self.start_time, 'end_time': self.end_time, 'title': f'clip_{self.start_time}-{self.end_time}'}
                ]
                ydl_opts['outtmpl'] = os.path.join(self.output_dir, f'{base_filename}_{self.start_time}s-{self.end_time}s.%(ext)s')
                
                # 对于时间段下载，增加重试次数
                ydl_opts['retries'] = 20
                ydl_opts['fragment_retries'] = 20
            
            # 确定下载格式
            if self.resolution_choice and self.resolution_choice != "auto":
                # 手动选择特定格式
                ydl_opts['format'] = self.resolution_choice
                print(f"手动选择格式: {self.resolution_choice}")
            else:
                # 自动选择最佳格式
                print("自动选择最佳视频格式")
            
            # 开始下载视频
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 重新获取信息（因为文件名模板可能改变了）
                info_dict = ydl.extract_info(self.url, download=False)
                
                self.signals.progress.emit(5, 100, "开始下载视频...")
                
                # 不再需要并行音频下载，因为视频已经包含音频
                # if hasattr(self, 'download_audio') and self.download_audio:
                #     print("🎵 并行开始下载音频...")
                #     # 创建音频工作器并异步执行
                #     audio_worker = AudioDownloadWorker(...)
                #     download_manager.thread_pool.start(audio_worker)
                
                # 下载视频（包含音频合并）
                ydl.download([self.url])
                
                actual_filename = ydl.prepare_filename(info_dict)
                video_filename = os.path.abspath(actual_filename)
                
                if os.path.exists(video_filename):
                    print(f"✅ 视频下载完成: {video_filename}")
                    self.signals.progress.emit(100, 100, "视频下载完成")
                    return video_filename
                else:
                    print("❌ 视频文件不存在")
                    self.signals.progress.emit(0, 100, "视频文件不存在")
                    return None
                    
        except Exception as e:
            error_msg = f"下载失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.signals.progress.emit(0, 100, error_msg)
            return None
            
    def _create_progress_hook(self):
            """创建进度钩子函数 - 自动清洗颜色代码版"""
            import re # 引入正则模块
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    # 1. 计算进度 (保持不变)
                    if 'total_bytes' in d and d['total_bytes']:
                        percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                        percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                    else:
                        if '_percent_str' in d and d['_percent_str']:
                            try:
                                percent_str = d['_percent_str'].strip().replace('%', '')
                                percent = float(percent_str)
                            except:
                                percent = 0
                        else:
                            percent = 0
                    
                    mapped_percent = int(percent)
                    
                    # 2. === 核心修改：清洗 ANSI 颜色代码 ===
                    # 定义一个正则，专门匹配 [0;32m 这种东西
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

                    raw_speed = d.get('_speed_str', 'N/A')
                    raw_eta = d.get('_eta_str', '')

                    # 清洗数据
                    speed = ansi_escape.sub('', str(raw_speed)).strip()
                    eta = ansi_escape.sub('', str(raw_eta)).strip()
                    
                    # 3. 构造简洁状态
                    status_msg = speed
                    if eta and eta != 'N/A':
                        status_msg += f" (剩 {eta})"
                        
                    self.signals.progress.emit(mapped_percent, 100, status_msg)
                    
                elif d['status'] == 'finished':
                    self.signals.progress.emit(100, 100, "分段写入完成")
                    
                elif d['status'] == 'error':
                    error_msg = f"下载流错误: {d.get('error', '未知')}"
                    self.signals.progress.emit(0, 100, error_msg)
            
            return progress_hook

class AudioDownloadWorker(DownloadWorker):
    """音频下载工作器"""
    
    def __init__(self, url, cookies_file=None, output_dir='downloads', 
                 start_time=None, end_time=None, resolution_choice=None,
                 system_proxy=None, headers=None, enable_quickjs=True):
        super().__init__(url, cookies_file, output_dir, start_time, end_time, resolution_choice)
        self.system_proxy = system_proxy
        self.headers = headers
        self.enable_quickjs = enable_quickjs # <--- 2. 保存到实例变量
    
    def run(self):
        """在工作线程中执行音频下载"""
        try:
            self.signals.started.emit()
            self.signals.progress.emit(0, 100, "准备下载音频...")
            
            result = self._download_audio()
            self.signals.finished.emit(result)
            
        except Exception as e:
            error_msg = f"音频下载失败: {e}"
            import traceback
            traceback.print_exc()
            self.signals.error.emit(error_msg)
            self.signals.finished.emit(None)
    
    def _download_audio(self):
        """实际的音频下载逻辑"""
        
        try:
            # 检查当前目录是否已经是downloads目录
            current_dir = os.getcwd()
            current_dir_name = os.path.basename(current_dir)
            
            # 如果当前目录已经是downloads，就直接使用当前目录
            if current_dir_name.lower() == 'downloads' or self.output_dir in current_dir:
                self.output_dir = current_dir
                print(f"使用当前目录作为输出目录: {self.output_dir}")
            else:
                if not os.path.exists(self.output_dir):
                    os.makedirs(self.output_dir)
                    print(f"创建输出目录: {self.output_dir}")
                else:
                    print(f"使用现有输出目录: {self.output_dir}")

            # 配置基础的 yt-dlp 选项
            ydl_opts = {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'noprogress': True,  # 禁用内置进度条，使用我们的钩子
                'quiet': False,
                'progress_hooks': [self._create_audio_progress_hook()],  # 使用进度钩子
                # 网络优化设置
                'retries': 10,
                'fragment_retries': 10,
                'skip_unavailable_fragments': True,
                'retry_sleep_functions': {
                    'http': lambda n: 5,
                    'ftp': lambda n: 5,
                    'file': lambda n: 2,
                },
                'buffersize': 1024 * 1024,
                'http_chunk_size': 10 * 1024 * 1024,
                'continuedl': True,
                'no_part': False,
            }

            if self.enable_quickjs:
                ydl_opts['js_runtimes'] = {
                    'quickjs': [qjs_exe_path]
                }
            
            # 添加代理、cookies和headers
            if self.system_proxy:
                ydl_opts['proxy'] = self.system_proxy
            if self.cookies_file:
                ydl_opts['cookiefile'] = self.cookies_file
            if self.headers:
                ydl_opts['http_headers'] = self.headers
            
            # 先获取视频信息来生成 base_filename
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.url, download=False)
            
            # 生成 base_filename
            base_filename = re.sub(r'[^\w\-_\. ]', '_', info_dict['title'])
            print(f"生成基础文件名: {base_filename}")
            
            print("🔊 开始下载音频...")
            
            self.signals.progress.emit(0, 100, "准备下载音频...")

            # 更新 yt-dlp 选项
            ydl_opts['outtmpl'] = os.path.join(self.output_dir, f'{base_filename}_audio.%(ext)s')
            
            # 添加时间段参数
            if self.start_time is not None and self.end_time is not None:
                ydl_opts['download_ranges'] = lambda info_dict, ydl: [
                    {'start_time': self.start_time, 'end_time': self.end_time, 'title': f'clip_{self.start_time}-{self.end_time}'}
                ]
                ydl_opts['outtmpl'] = os.path.join(self.output_dir, f'{base_filename}_audio_{self.start_time}s-{self.end_time}s.%(ext)s')
            
            # 添加音频后处理选项
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'aac',
                    'preferredquality': '192',
                }]
            })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.url, download=False)
                
                self.signals.progress.emit(5, 100, "开始下载音频...")
                
                ydl.download([self.url])
                
                # 准备文件名时需要考虑后处理后的扩展名变化
                actual_filename = ydl.prepare_filename(info_dict)
                # 由于使用了音频提取，实际文件名会变成 .mp3
                base_name = os.path.splitext(actual_filename)[0]
                audio_filename = base_name + '.mp3'
                
                if os.path.exists(audio_filename):
                    print(f"✅ 音频下载完成: {audio_filename}")
                    self.signals.progress.emit(100, 100, "音频下载完成")
                    return audio_filename
                else:
                    # 如果mp3文件不存在，尝试查找原始文件
                    if os.path.exists(actual_filename):
                        print(f"✅ 音频下载完成（原始格式）: {actual_filename}")
                        self.signals.progress.emit(100, 100, "音频下载完成")
                        return actual_filename
                    else:
                        print("❌ 音频文件不存在")
                        self.signals.progress.emit(0, 100, "音频文件不存在")
                        return None
                        
        except Exception as e:
            print(f"❌ 音频下载出错: {e}")
            import traceback
            traceback.print_exc()
            self.signals.progress.emit(0, 100, f"音频下载错误: {str(e)}")
            return None

    def _create_audio_progress_hook(self):
        """创建音频下载进度钩子函数"""
        def progress_hook(d):
            if d['status'] == 'downloading':
                # 计算下载进度百分比
                if 'total_bytes' in d and d['total_bytes']:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                else:
                    # 如果没有总大小信息，尝试从百分比字符串解析
                    if '_percent_str' in d and d['_percent_str']:
                        try:
                            percent_str = d['_percent_str'].strip().replace('%', '')
                            percent = float(percent_str)
                        except:
                            percent = 0
                    else:
                        percent = 0
                
                # 直接使用0-100%范围
                mapped_percent = int(percent)
                
                # 获取下载速度和ETA
                speed = d.get('_speed_str', '').strip()
                eta = d.get('_eta_str', '').strip()
                
                status_msg = f"下载音频: {percent:.1f}%"
                if speed:
                    status_msg += f" | 速度: {speed}"
                if eta:
                    status_msg += f" | 剩余: {eta}"
                    
                self.signals.progress.emit(mapped_percent, 100, status_msg)
                
            elif d['status'] == 'finished':
                self.signals.progress.emit(100, 100, "音频下载完成")
                print("✅ 音频下载完成")
                
            elif d['status'] == 'error':
                error_msg = f"音频下载错误: {d.get('error', '未知错误')}"
                print(f"❌ {error_msg}")
                self.signals.progress.emit(0, 100, error_msg)
        
        return progress_hook

class AsyncDownloadManager:
    """异步下载管理器"""
    
    def __init__(self):
        self.thread_pool = QThreadPool()
        cpu_count = multiprocessing.cpu_count()
        optimal_threads = max(2, min(cpu_count - 1, 4))  # 根据CPU核心数动态调整
        self.thread_pool.setMaxThreadCount(optimal_threads)
        self.active_workers = {}

        print(f"🔧 异步下载管理器初始化完成，最大线程数: {optimal_threads}")

        # 创建可复用的session
        self.session = self._create_session()

    def _create_session(self):
        """创建带连接池的session"""
        session = requests.Session()
        
        # 重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def fetch_formats(self, url, cookies_file=None):
        """异步获取格式信息"""
        worker = FormatFetchWorker(url, cookies_file)
        worker_id = id(worker)
        self.active_workers[worker_id] = worker
        self.thread_pool.start(worker)
        print(f"🎬 启动格式获取任务，当前活动任务: {len(self.active_workers)}")
        return worker
    
    def download_video(self, url, cookies_file=None, output_dir='downloads', 
                      start_time=None, end_time=None, resolution_choice=None,
                      system_proxy=None, headers=None):
        """异步下载视频"""
        worker = VideoDownloadWorker(url, cookies_file, output_dir, 
                                   start_time, end_time, resolution_choice,
                                   system_proxy, headers)
        worker_id = id(worker)
        self.active_workers[worker_id] = worker
        self.thread_pool.start(worker)
        print(f"🎬 启动视频下载任务，当前活动任务: {len(self.active_workers)}")
        return worker
    
    def download_audio(self, url, cookies_file=None, output_dir='downloads', 
                      start_time=None, end_time=None, resolution_choice=None,
                      system_proxy=None, headers=None):
        """异步下载音频"""
        worker = AudioDownloadWorker(
            url, cookies_file, output_dir, 
            start_time, end_time, resolution_choice,
            system_proxy, headers,
            enable_quickjs=False  # <--- 新增这行，强制禁用 JS 引擎
        )
        worker_id = id(worker)
        self.active_workers[worker_id] = worker
        self.thread_pool.start(worker)
        print(f"🎬 启动音频下载任务，当前活动任务: {len(self.active_workers)}")
        return worker
    
    def cancel_worker(self, worker):
        """取消任务"""
        worker_id = id(worker)
        if worker_id in self.active_workers:
            # 这里可以添加自定义取消逻辑
            # 例如在worker中设置一个_cancelled标志
            if hasattr(worker, 'cancel'):
                worker.cancel()
            
            del self.active_workers[worker_id]
            print(f"⏹️ 取消任务，剩余活动任务: {len(self.active_workers)}")

    def remove_worker(self, worker):
        """从活动任务中移除工作器"""
        worker_id = id(worker)
        if worker_id in self.active_workers:
            del self.active_workers[worker_id]
            print(f"🗑️ 移除任务，剩余活动任务: {len(self.active_workers)}")
    
    def wait_for_done(self, timeout=30000):
        """等待所有任务完成"""
        self.thread_pool.waitForDone(timeout)
    
    def active_count(self):
        """获取活动任务数量"""
        return self.thread_pool.activeThreadCount()
    
    def cleanup(self):
        """清理所有任务"""
        self.thread_pool.clear()
        self.active_workers.clear()
        print("🧹 清理所有下载任务")

# 创建全局下载管理器实例
download_manager = AsyncDownloadManager()