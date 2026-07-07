#!/bin/bash
# ================================================
#  Duplicate Image Finder - APK 一键构建脚本
#  在 WSL Ubuntu 中运行: bash build_apk.sh
# ================================================
set -e

echo "===== 1/4 安装系统依赖 ====="
sudo apt update -y
sudo apt install -y python3-pip openjdk-17-jdk git zip unzip autoconf libtool \
    libssl-dev libffi-dev zlib1g-dev libltdl-dev

echo ""
echo "===== 2/4 安装 Buildozer + Cython ====="
pip install --upgrade buildozer cython

echo ""
echo "===== 3/4 构建 APK (首次约 15-30 分钟，请耐心等待) ====="
buildozer android debug

echo ""
echo "===== 4/4 完成! ====="
APK_FILE=$(ls bin/*.apk 2>/dev/null | head -1)
if [ -n "$APK_FILE" ]; then
    echo "APK 已生成: $APK_FILE"
    echo ""
    echo "复制到 Windows 桌面:"
    echo "  cp $APK_FILE /mnt/c/Users/I/Desktop/"
    echo ""
    echo "然后通过 USB / 微信 / QQ / 网盘传到手机安装即可"
else
    echo "构建失败，请查看上方日志"
fi
