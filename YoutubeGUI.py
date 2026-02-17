import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import sys
import subprocess
import shutil
import time

# --- 全局变量 ---
yt_dlp = None
ffmpeg_available = False

# 调整 init_app 增加静默检查
def init_app():
    global yt_dlp, ffmpeg_available
    
    # 0. 静默检查更新
    threading.Thread(target=check_update_silent).start()
    
    log("正在初始化核心组件...")
    
    # 1. 检查/安装 yt-dlp
    if not ensure_ytdlp_installed():
        log("❌ 核心组件 yt-dlp 加载失败，程序无法使用。")
        return

    import yt_dlp as ydl_module
    yt_dlp = ydl_module
    log("✅ 核心组件加载完成。")

    # 2. 检查 FFmpeg
    ffmpeg_available = shutil.which("ffmpeg") is not None
    if ffmpeg_available:
        log("✅ 检测到 FFmpeg 组件，支持高清画质合并。")
    else:
        log("⚠️ 未检测到 FFmpeg！")
        log("👉 后果：无法下载 1080p+ 画质，所有视频将自动降级为兼容格式（通常是 720p 或更低）。")
        window.after(1000, lambda: messagebox.showwarning("画质受限警告", 
            "未检测到 FFmpeg 组件！\n\n导致后果：\n1. 无法合并视频流和音频流\n2. 下载的视频画质将受限（通常最高 720p）\n3. 文件大小可能异常小\n\n建议安装 FFmpeg 以解锁 1080p/4k 画质。"))

def ensure_ytdlp_installed():
    # 如果是打包后的环境，直接跳过检查
    if getattr(sys, 'frozen', False):
        try:
            import yt_dlp
            return True
        except ImportError:
            return False

    try:
        import yt_dlp
        return True
    except ImportError:
        log("正在尝试自动修复依赖...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "--break-system-packages"])
            return True
        except:
            return False

# --- 日志输出 ---
def log(message):
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    full_msg = f"[{timestamp}] {message}\n"
    window.after(0, lambda: _append_log(full_msg))

def _append_log(msg):
    log_area.config(state='normal')
    log_area.insert(tk.END, msg)
    log_area.see(tk.END) # 自动滚动到底部
    log_area.config(state='disabled')

def start_download():
    if yt_dlp is None:
        messagebox.showwarning("提示", "正在初始化组件，请稍后...")
        return

    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("提示", "请先粘贴视频链接！")
        return
    
    # 智能判断：如果未解析直接点下载，自动触发解析并下载最高画质
    if not quality_var.get():
        log("检测到未选择画质，正在自动解析并下载最佳画质...")
        # 这里为了简化逻辑，我们直接用Best配置启动下载任务，跳过手动选择
        # 但为了用户体验，最好还是走一遍解析流程，或者赋予默认值
        # 简单方案：赋予默认最高画质
        download_btn.config(state=tk.DISABLED, text="下载中...")
        thread = threading.Thread(target=run_download_task, args=(url, "1. 最高画质 (最佳效果)", path_entry.get().strip()))
        thread.start()
        return

    quality = quality_var.get()
    save_path = path_entry.get().strip()
    if not save_path or not os.path.isdir(save_path):
        messagebox.showwarning("提示", "请选择有效的保存路径！")
        return
    
    download_btn.config(state=tk.DISABLED, text="下载中...")
    log("🚀 开始下载任务...")

    thread = threading.Thread(target=run_download_task, args=(url, quality, save_path))
    thread.start()

def run_download_task(url, quality, save_path):
    # has_ffmpeg = check_ffmpeg() # 使用全局变量
    
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        # 'cookiesfrombrowser': ('safari',), 
        'merge_output_format': 'mp4',
        'noplaylist': True, 
        'progress_hooks': [progress_hook],
        'logger': MyLogger(), # 捕获 yt-dlp 内部日志
    }
    
    if not ffmpeg_available:
        log("⚠️ [兼容模式] 未检测到FFmpeg，将根据可用格式下载")
        if 'merge_output_format' in ydl_opts:
            del ydl_opts['merge_output_format'] # 没有ffmpeg无法合并，不能指定merge_output_format

    if "仅音频" in quality:
        if ffmpeg_available:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
             ydl_opts.update({'format': 'bestaudio/best'})
             window.after(0, lambda: messagebox.showinfo("提示", "无FFmpeg，下载原始音频"))

    elif "最高画质" in quality or "1." in quality: # 兼容带序号的选项
        if ffmpeg_available:
            ydl_opts.update({'format': 'bestvideo+bestaudio/best'})
        else:
            # 没有FFmpeg，强制只能下载 best（通常是720p或更低，已经包含音频的单个文件）
            ydl_opts.update({'format': 'best'}) 
            
    elif "标准画质" in quality: # 旧逻辑兼容
        ydl_opts.update({'format': 'best[height<=720][ext=mp4]/best[height<=720]'})

    # 处理带序号的选项 "2. 1080p xxx"
    elif any(x in quality for x in ["2.", "3.", "4.", "5."]):
        try:
            # 提取数字部分，例如 "2. 1080p" -> "1080"
            import re
            res_match = re.search(r'(\d+)p', quality)
            if res_match:
                res = res_match.group(1)
                if ffmpeg_available:
                    ydl_opts.update({'format': f'bestvideo[height<={res}]+bestaudio/best[height<={res}]'})
                else:
                    ydl_opts.update({'format': f'best[height<={res}]'})
        except:
            pass 

    try:
        log("正在连接下载服务器...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        window.after(0, lambda: download_finished(True))
    except Exception as e:
        log(f"❌ 下载发生异常: {str(e)}")
        window.after(0, lambda: download_finished(False, str(e)))

class MyLogger:
    def debug(self, msg):
        if not msg.startswith('[debug] '):
            # log(f"[内部] {msg}")
            pass
    def warning(self, msg):
        # 过滤掉一些不影响使用的警告
        if "challenge" in msg or "AppSupport" in msg:
            return 
        log(f"⚠️ {msg}")
    def error(self, msg):
        log(f"❌ {msg}")

def progress_hook(d):
    global last_percent
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%')
#         s = d.get('_speed_str', 'N/A')
        # 减少刷屏，只在整10%或者完成时记录
        s = d.get('_speed_str', 'N/A')
        # 减少刷屏，只在整10%或者完成时记录
        # 但为了让用户看到动静，还是实时更新log的最后一样比较好？
        # 这里我们就简单地每一段时间log一次，或者直接只更新Label，log里只记关键节点
        # 用户的需求是debug，所以最好详细一点
        # 这里用 window.after 更新到 log 可能会太快导致界面卡顿，所以只记录关键节点
        pass 
        # 实时速度还是显示在状态栏比较好，log里记录 milestones
    elif d['status'] == 'finished':
        log("✅ 文件下载完成，正在进行后期处理（合并/转码）...")

def download_finished(success, error_msg=""):
    download_btn.config(state=tk.NORMAL, text="立即下载")
    if success:
        log("🎉 所有任务执行成功！")
        messagebox.showinfo("成功", "视频下载完成！")
        try:
            subprocess.call(["open", path_entry.get()])
        except:
            pass
    else:
        log("❌ 任务失败")
        messagebox.showerror("错误", f"下载出错了：{error_msg}")

def analyze_url(url):
    if not url: return

    # 没加载完 yt-dlp 时点击也没用
    if yt_dlp is None:
        messagebox.showwarning("提示", "核心组件正在后台初始化，请稍后...")
        return
    
    log(f"🔍 正在解析视频信息: {url}")
    log("⏳ 请稍候，这可能需要几秒钟...")
    
    options_frame.pack_forget()

    def run_analysis():
        try:
            ydl_opts = {
                'noplaylist': True,
                'quiet': True,
                # 'cookiesfrombrowser': ('safari',), # 移除复杂鉴权
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            video_title = info.get('title', '未知标题')
            
            formats = info.get('formats', [])
            resolutions = set()
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('height'):
                    resolutions.add(f['height'])
            
            # 排序：从高到低
            sorted_res = sorted(list(resolutions), reverse=True)
            
            # 构建带序号的选项列表
            options = ["1. 最高画质 (最佳效果)"]
            
            idx = 2
            for r in sorted_res:
                options.append(f"{idx}. {r}p (MP4)")
                idx += 1
                
            options.append(f"{idx}. 仅音频 (MP3)")
            
            # 回到主线程更新 UI
            window.after(0, lambda: update_success(options, video_title))
            
        except Exception as e:
            err_msg = str(e)
            window.after(0, lambda: update_fail(err_msg))

    threading.Thread(target=run_analysis).start()

def update_success(options, title):
    log(f"✅ 解析成功: {title}")
    quality_menu['values'] = options
    quality_menu.current(0)
    
    # 更新标题显示
    title_label.config(text=f"📺 视频标题：{title}")
    log("请选择画质和保存路径，然后点击下载。")
    
    options_frame.pack(pady=10, fill=tk.X, padx=20)

def update_fail(err):
    log(f"❌ 解析失败: {err}")
    log("提示：可能是网络问题，或该视频有限制。")
    messagebox.showerror("错误", "无法解析该视频链接。\n请检查网络或链接是否正确。")

# --- 窗口界面布局与主题 ---
LIGHT_THEME = {
    "bg": "#FFFFFF",
    "fg": "#333333",
    "entry_bg": "#FFFFFF",
    "btn_bg": "#F0F0F0",
    "highlight": "#CCCCCC",
    "log_bg": "#FFFFFF",
    "btn_text": "🌙 切换黑暗模式"
}

DARK_THEME = {
    "bg": "#1E1E1E",
    "fg": "#EEEEEE",
    "entry_bg": "#2D2D2D",
    "btn_bg": "#3D3D3D",
    "highlight": "#444444",
    "log_bg": "#2D2D2D",
    "btn_text": "☀️ 切换明亮模式"
}

current_theme = LIGHT_THEME # 默认明亮

def toggle_theme():
    global current_theme
    current_theme = DARK_THEME if current_theme == LIGHT_THEME else LIGHT_THEME
    apply_theme()

def apply_theme():
    theme = current_theme
    window.config(bg=theme["bg"])
    
    # ttk Style for Combobox
    s = ttk.Style()
    s.theme_use('clam')
    s.configure('TCombobox', fieldbackground=theme["entry_bg"], background=theme["btn_bg"], foreground=theme["fg"], selectbackground=theme["btn_bg"], selectforeground=theme["fg"])
    s.map('TCombobox', fieldbackground=[('readonly', theme["entry_bg"])], background=[('readonly', theme["btn_bg"])])
    
    def update_widget(parent):
        for widget in parent.winfo_children():
            w_type = widget.winfo_class()
            
            if w_type == "Frame":
                widget.config(bg=theme["bg"])
                update_widget(widget)
            elif w_type == "Label":
                # 特殊处理模拟按钮的 Label
                if widget in [paste_btn, browse_label]:
                    widget.config(bg=theme["btn_bg"], fg=theme["fg"], padx=20, pady=10)
                else:
                    widget.config(bg=theme["bg"], fg=theme["fg"])
            elif w_type == "Button":
                if widget == download_btn:
                    # 下载按钮使用显眼的红色
                    widget.config(highlightbackground="#FF0000", fg="black")
                elif widget in [theme_btn, update_btn]:
                    widget.config(bg=theme["bg"], fg="#999999", highlightbackground=theme["bg"],
                                  text=theme["btn_text"] if widget == theme_btn else widget.cget("text"))
                else:
                    widget.config(highlightbackground=theme["btn_bg"], fg=theme["fg"])
                widget.config(highlightthickness=2, borderwidth=0)
            elif w_type == "Entry":
                widget.config(bg=theme["entry_bg"], fg=theme["fg"], highlightbackground=theme["highlight"], insertbackground=theme["fg"], highlightthickness=1)
            elif "Text" in w_type:
                widget.config(bg=theme["log_bg"], fg=theme["fg"], highlightbackground=theme["highlight"])

    update_widget(window)
    # 强制刷新一些关键容器
    for f in [header_frame, content_frame, entry_frame, options_frame, path_frame, log_frame]:
        try: f.config(bg=theme["bg"])
        except: pass

window = tk.Tk()
window.title("YouTube 极简下载器 v1.1.1")
window.geometry("700x1000") # 增加高度，防止内容被遮挡
window.minsize(600, 600)
# window.config(bg=BG_COLOR) # Initial config will be handled by apply_theme

# 尝试调用 macOS 原生 API 实现统一标题栏 (如果可用)
try:
    # 这一行代码会让窗口背景延伸到标题栏，实现"沉浸式"效果
    window.tk.call('::tk::unsupported::MacWindowStyle', 'style', window, 'unified')
except:
    pass

import json
import urllib.request

CURRENT_VERSION = "v1.1.2"
UPDATE_URL = "https://github.com/pk197197/youtube-downloader/releases"
API_URL = "https://api.github.com/repos/pk197197/youtube-downloader/releases/latest"
CONFIG_FILE = os.path.expanduser("~/.youtube_downloader_config.json")

class ConfigManager:
    @staticmethod
    def load():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"skipped_version": "", "auto_check": True}

    @staticmethod
    def save(config):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except:
            pass

class UpdateDialog(tk.Toplevel):
    def __init__(self, parent, version_info):
        super().__init__(parent)
        self.title("发现新版本")
        self.geometry("600x400")
        self.resizable(False, False)
        
        # 居中显示
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

        # 内容布局
        tk.Label(self, text=f"发现新版本: {version_info['tag_name']}", font=("Arial", 16, "bold")).pack(pady=(20, 10))
        tk.Label(self, text=f"当前版本: {CURRENT_VERSION}", fg="gray").pack()
        
        # 更新日志区域
        text_frame = tk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        text_area = scrolledtext.ScrolledText(text_frame, height=10, font=("Arial", 12))
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, version_info.get('body', '暂无更新日志'))
        text_area.config(state='disabled')
        
        # 按钮区域
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.config_data = ConfigManager.load()
        self.var_auto_check = tk.BooleanVar(value=self.config_data.get("auto_check", True))
        
        # 自动检查勾选框
        tk.Checkbutton(btn_frame, text="启动时自动检查更新", variable=self.var_auto_check, 
                       command=self.save_auto_check).pack(side=tk.LEFT)
        
        # 统一按钮样式生成函数
        def create_btn(parent, text, command, bg_color, fg_color, hover_color):
            btn = tk.Label(parent, text=text, font=("Arial", 12), 
                           bg=bg_color, fg=fg_color, cursor="hand2", padx=15, pady=6)
            btn.pack(side=tk.RIGHT, padx=5)
            btn.bind("<Button-1>", lambda e: command())
            
            def on_enter(e): btn.config(bg=hover_color)
            def on_leave(e): btn.config(bg=bg_color)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            return btn

        # 1. 立即更新 (Primary - Blue)
        create_btn(btn_frame, "立即更新 🚀", lambda: self.do_update(version_info['html_url']), 
                   "#007AFF", "white", "#005BB5")

        # 2. 稍后提醒 (Secondary - Light Gray)
        create_btn(btn_frame, "稍后提醒", self.destroy, 
                   "#F0F0F0", "#333333", "#E0E0E0")
        
        # 3. 跳过 (Secondary - Light Gray - Consistent Style)
        create_btn(btn_frame, "跳过此版本", lambda: self.skip_version(version_info['tag_name']), 
                   "#F0F0F0", "#333333", "#E0E0E0")

    def save_auto_check(self):
        self.config_data['auto_check'] = self.var_auto_check.get()
        ConfigManager.save(self.config_data)

    def skip_version(self, version):
        self.config_data['skipped_version'] = version
        ConfigManager.save(self.config_data)
        self.destroy()

    def do_update(self, url):
        webbrowser.open(url)
        self.destroy()

def check_update_silent():
    config = ConfigManager.load()
    if not config.get("auto_check", True):
        return

    try:
        with urllib.request.urlopen(API_URL, timeout=5) as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name']
            
            # 如果是新版本 且 没有被跳过
            if latest_version != CURRENT_VERSION and latest_version != config.get("skipped_version"):
                window.after(0, lambda: UpdateDialog(window, data))
    except:
        pass

def check_update_manual():
    log("正在检查更新...")
    try:
        with urllib.request.urlopen(API_URL, timeout=5) as response:
            data = json.loads(response.read().decode())
            latest_version = data['tag_name']
            
            if latest_version != CURRENT_VERSION:
                window.after(0, lambda: UpdateDialog(window, data))
            else:
                window.after(0, lambda: messagebox.showinfo("检查更新", "当前已是最新版本！"))
                log("✅ 当前已是最新版本。")
    except Exception as e:
        log(f"❌ 检查更新失败: {e}")
        window.after(0, lambda: messagebox.showerror("错误", "检查更新失败，请检查网络。"))

default_font = ("Arial", 14)
title_font = ("Arial", 28, "bold")
label_font = ("Arial", 16, "bold") # 加粗标签
window.option_add('*TCombobox*Listbox.font', default_font)

import webbrowser

# 替换旧的 check_update
def check_update():
    threading.Thread(target=check_update_manual).start()

# 1. 顶部区域 (留白与功能按钮)
header_frame = tk.Frame(window)
header_frame.pack(pady=(40, 20), fill=tk.X, padx=30) 

# 右上角功能按钮组
btn_container = tk.Frame(header_frame)
btn_container.pack(side=tk.RIGHT)

update_btn = tk.Button(btn_container, text=f"检查更新 {CURRENT_VERSION}", command=check_update, 
          font=("Arial", 11), relief="flat", cursor="hand2")
update_btn.pack(side=tk.RIGHT)

# 黑暗模式切换按钮
theme_btn = tk.Button(btn_container, text="🌙 切换黑暗模式", command=toggle_theme,
          font=("Arial", 11), relief="flat", cursor="hand2")
theme_btn.pack(side=tk.RIGHT, padx=(0, 15))

# 2. 链接输入区域 (模拟卡片式设计)
content_frame = tk.Frame(window)
content_frame.pack(fill=tk.BOTH, expand=True, padx=40)

tk.Label(content_frame, text="在此粘贴视频链接", font=("Arial", 24, "bold")).pack(pady=(20, 15))

# 使用 Frame 来做边框效果
entry_frame = tk.Frame(content_frame)
entry_frame.pack(pady=5, padx=20, fill=tk.X)

url_entry = tk.Entry(entry_frame, font=("Arial", 16), relief="flat")
url_entry.pack(fill=tk.X, ipady=8) # 增加内部高度

def paste_link(event=None):
    try:
        content = window.clipboard_get()
        url_entry.delete(0, tk.END)
        url_entry.insert(0, content)
        analyze_url(content)
    except:
        pass

def on_enter(event):
    event.widget.config(bg=current_theme["highlight"])

def on_leave(event):
    event.widget.config(bg=current_theme["btn_bg"])

# 使用 Label 模拟按钮，彻底解决 macOS 颜色问题
paste_btn = tk.Label(content_frame, text="📋 点击这里一键粘贴并解析", font=default_font, 
                     relief="flat", cursor="hand2", padx=20, pady=10)
paste_btn.pack(pady=10)
paste_btn.bind("<Button-1>", paste_link)
paste_btn.bind("<Enter>", on_enter)
paste_btn.bind("<Leave>", on_leave)

# 3. 选项区域 (中间部分) - 放在 content_frame 里面
options_frame = tk.Frame(content_frame)
# 注意：options_frame 在 analyze_url 中会被 pack，这里只需要保留定义

# 3.0 视频标题显示
title_label = tk.Label(options_frame, text="视频标题：...", font=("Arial", 14, "bold"), wraplength=550)
title_label.pack(pady=(10, 10))

# 3.1 画质/格式选择
tk.Label(options_frame, text="第二步：选择画质/格式", font=label_font).pack(pady=(5, 5))
quality_var = tk.StringVar()
quality_menu = ttk.Combobox(options_frame, textvariable=quality_var, state="readonly", font=default_font)
quality_menu.pack(pady=5, padx=30, fill=tk.X, ipady=5)

# 3.2 保存路径选择
tk.Label(options_frame, text="第三步：保存位置", font=label_font).pack(pady=(15, 5))
path_frame = tk.Frame(options_frame)
path_frame.pack(pady=5, padx=30, fill=tk.X)

path_entry = tk.Entry(path_frame, font=default_font, relief="flat")
path_entry.insert(0, os.path.expanduser("~/Downloads"))
path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

def choose_path(event=None):
    path = filedialog.askdirectory()
    if path:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, path)

# 同样使用 Label 模拟浏览按钮
browse_label = tk.Label(path_frame, text="📂 浏览...", font=default_font, cursor="hand2", padx=10)
browse_label.pack(side=tk.RIGHT, padx=(5, 0))
browse_label.bind("<Button-1>", choose_path)
browse_label.bind("<Enter>", on_enter)
browse_label.bind("<Leave>", on_leave)

# 4. 下载按钮 (保持 Button，但确保颜色正确)
download_btn = tk.Button(options_frame, text="立即下载", command=start_download, 
                         font=("Arial", 18, "bold"), height=2) 
download_btn.pack(pady=30, padx=30, fill=tk.X)

# 5. 日志显示区域 (固定在底部)
log_frame = tk.Frame(window)
log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=20, pady=20)

tk.Label(log_frame, text="运行日志 / 进度：", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
log_area = scrolledtext.ScrolledText(log_frame, height=8, font=("Courier", 12), state='disabled', 
                                     relief="flat", highlightthickness=1)
log_area.pack(fill=tk.BOTH, expand=True)

log("程序已就绪，请粘贴链接或点击按钮开始。")

# 初始化UI主题
apply_theme()

# 启动后台初始化线程 (加速启动)
threading.Thread(target=init_app, daemon=True).start()

window.mainloop()