import subprocess
import os
import shutil
import sys
import re

APP_NAME = "YouTube极简下载器"

# 从主程序提取版本号
with open("YoutubeGUI.py", "r", encoding="utf-8") as f:
    content = f.read()
    match = re.search(r'CURRENT_VERSION\s*=\s*"(.*?)"', content)
    VERSION = match.group(1) if match else "v1.0"

DMG_NAME = f"{APP_NAME}_{VERSION}_macOS.dmg"
VOLUME_NAME = f"{APP_NAME} Installer"
SOURCE_APP = f"dist/{APP_NAME}.app"

def create_dmg():
    print(f"🚀 开始创建 DMG 打包镜像: {DMG_NAME}...")
    
    # 1. 检查基础环境
    if sys.platform != "darwin":
        print("❌ 错误: DMG 只能在 macOS 上创建。")
        return

    if not os.path.exists(SOURCE_APP):
        print(f"❌ 错误: 找不到 {SOURCE_APP}。请先运行 build_app.py")
        return

    # 2. 清理旧文件
    if os.path.exists(DMG_NAME):
        print(f"🧹 清理旧的 DMG: {DMG_NAME}")
        os.remove(DMG_NAME)
    
    temp_dir = "dmg_temp"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # 3. 准备内容
    print("📂 正在准备镜像内容...")
    # 复制 .app
    shutil.copytree(SOURCE_APP, os.path.join(temp_dir, f"{APP_NAME}.app"), symlinks=True)
    # 创建 /Applications 快捷方式
    os.symlink("/Applications", os.path.join(temp_dir, "Applications"))
    
    # 4. 生成 DMG
    print("💿 正在调用 hdiutil 生成 DMG 文件 (这可能需要几秒钟)...")
    cmd = [
        "hdiutil", "create",
        "-volname", VOLUME_NAME,
        "-srcfolder", temp_dir,
        "-ov",
        "-format", "UDZO",
        DMG_NAME
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ 成功! DMG 已生成: {os.path.abspath(DMG_NAME)}")
        print(f"💡 现在您可以将此 DMG 文件上传到 GitHub Release 了。")
    except subprocess.CalledProcessError as e:
        print(f"❌ 生成失败: {e.stderr.decode()}")
    finally:
        # 5. 清理临时文件夹
        print("🧹 清理临时文件夹...")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    create_dmg()
