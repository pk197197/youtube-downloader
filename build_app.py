import subprocess
import sys
import os

def install_pyinstaller():
    print("Installing PyInstaller...")
    try:
        # 尝试检查是否已经安装
        subprocess.check_call([sys.executable, "-m", "pip", "show", "pyinstaller"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("PyInstaller already installed.")
        return
    except subprocess.CalledProcessError:
        pass

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    except subprocess.CalledProcessError:
        print("Standard install failed, trying with --break-system-packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "--break-system-packages"])

def build_app():
    print("Building .app bundle...")
    # --noconsole: 不显示终端窗口
    # --windowed: macOS .app 格式
    # --onefile: 打包成单个文件
    # --clean: 清理缓存
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--noconsole",
        "--windowed",
        "--onefile",
        "--clean",
        "--name", "YouTube极简下载器",
        "YoutubeGUI.py"
    ]
    subprocess.check_call(cmd)

if __name__ == "__main__":
    try:
        install_pyinstaller()
        build_app()
        print("\n" + "="*50)
        print("打包完成！")
        print(f"你的 App 在这个文件夹里: {os.path.join(os.getcwd(), 'dist', 'YouTube极简下载器.app')}")
        print("你可以直接双击运行它，或者把它拖到应用程序文件夹。")
        print("="*50)
        
        # 自动打开文件夹
        subprocess.call(["open", os.path.join(os.getcwd(), "dist")])
    except Exception as e:
        print(f"打包出错: {e}")
