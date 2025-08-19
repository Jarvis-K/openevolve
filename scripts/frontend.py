import asyncio
import os
import tempfile
from pathlib import Path

import streamlit as st
from openevolve import OpenEvolve
from openevolve.config import load_config

st.set_page_config(page_title="OpenEvolve - Algorithm Evolution Platform", page_icon="🧬", layout="wide")
st.title("🧬 OpenEvolve")
st.caption("Professional Algorithm Evolution Platform")

# Apply a professional light theme
st.markdown(
    """
    <style>
    .stApp {
        background-color: #ffffff;
        color: #2c3e50;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    h1 {
        color: #1e293b;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    h2, h3, h4, h5, h6 {
        color: #334155;
        font-weight: 600;
    }
    .stSelectbox label, .stTextInput label, .stNumberInput label {
        color: #475569;
        font-weight: 500;
        font-size: 0.875rem;
        margin-bottom: 0.25rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        transform: translateY(-1px);
        box-shadow: 0 6px 12px -1px rgba(59, 130, 246, 0.4);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #3b82f6;
        color: white;
    }
    .stTextInput > div > div > input, .stSelectbox > div > div > select {
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 0.5rem 0.75rem;
        font-size: 0.875rem;
    }
    .stTextInput > div > div > input:focus, .stSelectbox > div > div > select:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Run Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")

    st.subheader("Initial Program")
    init_path_tab, init_upload_tab = st.tabs(["Path", "Upload"])
    with init_path_tab:
        initial_path = st.text_input(
            "Initial program path",
            "examples/circle_packing/initial_program.py",
        )
    with init_upload_tab:
        initial_upload = st.file_uploader("Initial program (.py)", type=["py"], key="init_upload")

    st.subheader("Evaluator")
    eval_path_tab, eval_upload_tab = st.tabs(["Path", "Upload"])
    with eval_path_tab:
        eval_path = st.text_input(
            "Evaluator path",
            "examples/circle_packing/evaluator.py",
        )
    with eval_upload_tab:
        eval_upload = st.file_uploader("Evaluation script (.py)", type=["py"], key="eval_upload")

    st.subheader("Config")
    cfg_path_tab, cfg_upload_tab = st.tabs(["Path", "Upload"])
    with cfg_path_tab:
        config_path = st.text_input(
            "Config path (optional)",
            "examples/circle_packing/config_phase_1.yaml",
        )
    with cfg_upload_tab:
        config_upload = st.file_uploader("Config (YAML)", type=["yaml", "yml"], key="cfg_upload")

    iterations = st.number_input("Iterations", min_value=1, value=10)
    target_score = st.number_input("Target score", value=0.0, step=0.1)
    run_clicked = st.button("Run Evolution")

status = st.empty()

if run_clicked:
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        init_prog = tmpdir / "initial_program.py" if initial_upload else Path(initial_path)
        if initial_upload:
            init_prog.write_bytes(initial_upload.getbuffer())
        eval_prog = tmpdir / "evaluator.py" if eval_upload else Path(eval_path)
        if eval_upload:
            eval_prog.write_bytes(eval_upload.getbuffer())
        cfg_file = None
        if config_upload:
            cfg_file = tmpdir / "config.yaml"
            cfg_file.write_bytes(config_upload.getbuffer())
        elif config_path:
            cfg_file = Path(config_path)

        status.info("Running evolution...")
        try:
            config = load_config(cfg_file) if cfg_file else None
            openevolve = OpenEvolve(
                initial_program_path=str(init_prog),
                evaluation_file=str(eval_prog),
                config=config,
                config_path=None if config or cfg_file is None else str(cfg_file),
            )
            best_program = asyncio.run(
                openevolve.run(iterations=int(iterations), target_score=target_score)
            )
            status.success("Evolution complete!")
            st.subheader("Best Program Metrics")
            st.json(best_program.metrics)
        except Exception as e:
            status.error(str(e))
