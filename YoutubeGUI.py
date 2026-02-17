import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import sys
import subprocess
import shutil
import time

# --- 自动安装 yt-dlp ---
def ensure_ytdlp_installed():
    # 如果是打包后的环境，直接跳过检查
    if getattr(sys, 'frozen', False):
        try:
            import yt_dlp
            return True
        except ImportError:
            messagebox.showerror("错误", "内置的 yt-dlp 库丢失，请重新下载软件。")
            return False

    global yt_dlp
    try:
        import yt_dlp
        return True
    except ImportError:
        print("yt-dlp 未安装，正在尝试自动安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
            import yt_dlp
            return True
        except subprocess.CalledProcessError:
            print("普通安装失败，尝试 --break-system-packages...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "--break-system-packages"])
                import yt_dlp
                return True
            except Exception as e:
                messagebox.showerror("依赖缺失", f"无法自动安装 yt-dlp 库：\n{e}\n请手动运行: pip install yt-dlp --break-system-packages")
                return False
        except Exception as e:
            messagebox.showerror("依赖缺失", f"无法自动安装 yt-dlp 库：\n{e}\n请手动运行: pip install yt-dlp")
            return False

ensure_ytdlp_installed()

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

# --- 检查 FFmpeg ---
def check_ffmpeg():
    return shutil.which("ffmpeg") is not None

def start_download():
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("提示", "请先粘贴视频链接！")
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
    has_ffmpeg = check_ffmpeg()
    
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        # 'cookiesfrombrowser': ('safari',), 
        'merge_output_format': 'mp4',
        'noplaylist': True, 
        'progress_hooks': [progress_hook],
        'logger': MyLogger(), # 捕获 yt-dlp 内部日志
    }
    
    if not has_ffmpeg:
        log("⚠️ 未检测到FFmpeg，自动切换到兼容模式（单文件下载）")
        if 'merge_output_format' in ydl_opts:
            del ydl_opts['merge_output_format']

    if "仅音频" in quality:
        if has_ffmpeg:
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
             window.after(0, lambda: messagebox.showinfo("提示", "未安装FFmpeg，将下载原始音频(m4a/webm)"))

    elif "最高画质" in quality:
        if has_ffmpeg:
            ydl_opts.update({'format': 'bestvideo+bestaudio/best'})
        else:
            ydl_opts.update({'format': 'best[ext=mp4]/best'})

    elif "标准画质" in quality and "720p" in quality:
        if has_ffmpeg:
            ydl_opts.update({'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]'})
        else:
            ydl_opts.update({'format': 'best[height<=720][ext=mp4]/best[height<=720]'})

    elif "(" in quality and ")" in quality: 
        try:
            res = quality.split("p")[0].strip()
            if res.isdigit():
                 if has_ffmpeg:
                    ydl_opts.update({'format': f'bestvideo[height<={res}]+bestaudio/best[height<={res}]'})
                 else:
                    ydl_opts.update({'format': f'best[height<={res}][ext=mp4]'})
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
        log(f"⚠️ {msg}")
    def error(self, msg):
        log(f"❌ {msg}")

def progress_hook(d):
    global last_percent
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%')
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

    log(f"🔍 开始解析链接: {url}")
    options_frame.pack_forget()

    def run_analysis():
        try:
            ydl_opts = {
                'noplaylist': True,
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            video_title = info.get('title', '未知标题')
            log(f"✅ 解析成功: {video_title}")
            
            formats = info.get('formats', [])
            resolutions = set()
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('height'):
                    resolutions.add(f['height'])
            
            sorted_res = sorted(list(resolutions), reverse=True)
            options = ["1. 最高画质 (MP4)"]
            for r in sorted_res:
                options.append(f"{r}p (MP4)")
            options.append("仅音频 (MP3)")
            
            window.after(0, lambda: update_quality_menu(options, video_title))
        except Exception as e:
            log(f"❌ 解析失败: {e}")
            window.after(0, lambda: update_quality_menu(None, None))

    threading.Thread(target=run_analysis).start()

def update_quality_menu(options, title):
    if options:
        quality_menu['values'] = options
        quality_menu.current(0)
        
        # 更新标题显示
        title_label.config(text=f"📺 视频标题：{title}")
        log("请选择画质和保存路径，然后点击下载。")
        
        options_frame.pack(pady=10, fill=tk.X, padx=20)
    else:
        log("⚠️ 解析失败，请检查链接或网络。")
        messagebox.showerror("错误", "无法解析该视频链接。")

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

default_font = ("Arial", 14)
title_font = ("Arial", 28, "bold")
label_font = ("Arial", 16, "bold") # 加粗标签
window.option_add('*TCombobox*Listbox.font', default_font)

import webbrowser

CURRENT_VERSION = "v1.1.1"
UPDATE_URL = "https://github.com/pk197197/youtube-downloader/releases" # 更新为真实地址

def check_update():
    """打开浏览器前往下载页面"""
    if messagebox.askyesno("检查更新", f"当前版本: {CURRENT_VERSION}\n是否打开下载页面查看新版本？"):
        webbrowser.open(UPDATE_URL)

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

# 初始化主题
apply_theme()

window.mainloop()