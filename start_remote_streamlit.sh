#!/bin/bash

# 启动远程访问的Streamlit应用
echo "启动OpenEvolve远程可视化服务..."

# 设置环境变量
export STREAMLIT_SERVER_ADDRESS="0.0.0.0"

# 启动streamlit应用
streamlit run scripts/improved_frontend.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true

echo "服务已启动，可通过远程浏览器访问"