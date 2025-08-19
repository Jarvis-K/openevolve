import asyncio
import os
import tempfile
from pathlib import Path

import streamlit as st
from openevolve import OpenEvolve
from openevolve.config import load_config

st.set_page_config(page_title="AlgoArts", page_icon="🎨", layout="wide")
st.title("AlgoArts")
st.caption("Streamlined interface for algorithm evolution")

with st.sidebar:
    st.header("Run Configuration")
    api_key = st.text_input("OpenAI API Key", type="password")

    st.subheader("Initial Program")
    init_path_tab, init_upload_tab = st.tabs(["Path", "Upload"])
    with init_path_tab:
        initial_path = st.text_input(
            "Initial program path",
            "examples/function_minimization/initial_program.py",
        )
    with init_upload_tab:
        initial_upload = st.file_uploader("Initial program (.py)", type=["py"], key="init_upload")

    st.subheader("Evaluator")
    eval_path_tab, eval_upload_tab = st.tabs(["Path", "Upload"])
    with eval_path_tab:
        eval_path = st.text_input(
            "Evaluator path",
            "examples/function_minimization/evaluator.py",
        )
    with eval_upload_tab:
        eval_upload = st.file_uploader("Evaluation script (.py)", type=["py"], key="eval_upload")

    st.subheader("Config")
    cfg_path_tab, cfg_upload_tab = st.tabs(["Path", "Upload"])
    with cfg_path_tab:
        config_path = st.text_input(
            "Config path (optional)",
            "examples/function_minimization/config.yaml",
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
