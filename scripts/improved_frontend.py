import asyncio
import os
import tempfile
import threading
import time
import subprocess
from pathlib import Path

import streamlit as st
from openevolve import OpenEvolve
from openevolve.config import load_config
import streamlit.components.v1 as components

st.set_page_config(
    page_title="OpenEvolve - 算法演化平台", 
    page_icon="🧬", 
    layout="wide"
)

# 初始化状态
if 'evolution_running' not in st.session_state:
    st.session_state.evolution_running = False
if 'visualizer_process' not in st.session_state:
    st.session_state.visualizer_process = None

def start_visualizer():
    if st.session_state.visualizer_process is None:
        try:
            cmd = ["python3", "scripts/visualizer.py", "--path", "demo_evolution_data", "--host", "0.0.0.0", "--port", "8081"]
            st.session_state.visualizer_process = subprocess.Popen(cmd)
            time.sleep(2)
            return True
        except Exception as e:
            st.error(f"启动可视化器失败: {e}")
            return False
    return True

def stop_visualizer():
    # Check if session_state exists and has the attribute
    if hasattr(st, 'session_state') and hasattr(st.session_state, 'visualizer_process') and st.session_state.visualizer_process:
        st.session_state.visualizer_process.terminate()
        st.session_state.visualizer_process = None

# 标题
st.title("🧬 OpenEvolve 算法演化平台")
st.caption("专业的算法自动演化与可视化平台")

# 样式
st.markdown("""
<style>
    .stApp {
        font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("🔧 运行配置")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.subheader("📝 初始程序")
    initial_path = st.text_input("初始程序路径", "examples/circle_packing/initial_program.py")
    
    st.subheader("⚖️ 评估器")
    eval_path = st.text_input("评估器路径", "examples/circle_packing/evaluator.py")
    
    st.subheader("⚙️ 配置")
    config_path = st.text_input("配置文件路径", "examples/circle_packing/config_phase_1.yaml")
    
    iterations = st.number_input("迭代次数", min_value=1, value=10)
    target_score = st.number_input("目标分数", value=0.0, step=0.1)
    
    run_clicked = st.button("🚀 开始演化", type="primary")

# 主内容
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📊 演化可视化")
    
    if st.session_state.evolution_running:
        if start_visualizer():
            # 动态获取当前访问的主机地址
            # 从浏览器的URL中提取主机地址
            components.html("""
                <script>
                var currentHost = window.location.hostname;
                var visualizerUrl = 'http://' + currentHost + ':8081';
                document.write('<iframe src="' + visualizerUrl + '" width="100%" height="600px" frameborder="0"></iframe>');
                </script>
            """, height=600)
        else:
            st.error("无法启动可视化器")
    else:
        st.info("请配置参数并开始演化以查看可视化")

with col2:
    st.subheader("📈 演化状态")
    
    if st.session_state.evolution_running:
        st.success("🟢 演化进行中")
        if st.button("⏹️ 停止演化"):
            st.session_state.evolution_running = False
            stop_visualizer()
            st.rerun()
    else:
        st.info("⚪ 等待启动")

# 运行逻辑
if run_clicked:
    if not api_key:
        st.error("请输入OpenAI API Key")
    else:
        os.environ["OPENAI_API_KEY"] = api_key
        st.session_state.evolution_running = True
        
        def run_evolution():
            try:
                config = load_config(config_path) if config_path else None
                openevolve = OpenEvolve(
                    initial_program_path=initial_path,
                    evaluation_file=eval_path,
                    config=config
                )
                asyncio.run(openevolve.run(iterations=iterations, target_score=target_score))
                st.session_state.evolution_running = False
            except Exception as e:
                st.error(f"演化失败: {e}")
                st.session_state.evolution_running = False
        
        threading.Thread(target=run_evolution, daemon=True).start()
        st.success("演化已启动！")
        st.rerun()

# 清理
import atexit
atexit.register(stop_visualizer)
