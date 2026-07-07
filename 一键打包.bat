@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   重复图片查找器 - APK 一键打包工具
echo ========================================
echo.
echo 第一步: 安装 Ubuntu (如已安装会自动跳过)
echo ========================================
wsl --install -d Ubuntu --no-launch
echo.
echo 安装完成后，请手动打开 Ubuntu 应用。
echo 打开后，粘贴以下命令 (一行行来):
echo.
echo   sudo apt update
echo   sudo apt install -y python3-pip openjdk-17-jdk git zip unzip autoconf libtool libssl-dev libffi-dev zlib1g-dev
echo   pip install buildozer cython
echo   cp -r /mnt/c/Users/I/Desktop/DuplicateImageFinder ~/
echo   cd ~/DuplicateImageFinder
echo   buildozer android debug
echo.
echo 等半小时后，APK 在 bin/ 目录里
echo.
pause
