#!/bin/bash
# 启动脚本

echo "正在启动报名数据统计系统..."
echo "请确保已将Excel文件放在当前目录下"
echo ""
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务器"
echo ""

python3 app.py

