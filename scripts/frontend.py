import asyncio
import streamlit as st
from openevolve import OpenEvolve
from openevolve.config import load_config

st.title("OpenEvolve Frontend")

initial_program = st.text_input(
    "Initial program path",
    "examples/function_minimization/initial_program.py",
)

evaluation_file = st.text_input(
    "Evaluation file path",
    "examples/function_minimization/evaluator.py",
)

config_path = st.text_input(
    "Config path (optional)",
    "examples/function_minimization/config.yaml",
)

iterations = st.number_input("Iterations", min_value=1, value=10)

target_score = st.number_input("Target score", value=0.0, step=0.1)

if st.button("Run Evolution"):
    st.write("Running evolution...")
    try:
        config = load_config(config_path) if config_path else None
        openevolve = OpenEvolve(
            initial_program_path=initial_program,
            evaluation_file=evaluation_file,
            config=config,
            config_path=None if config else config_path,
        )
        best_program = asyncio.run(
            openevolve.run(iterations=int(iterations), target_score=target_score)
        )
        st.success("Evolution complete!")
        st.write("Best program metrics:")
        for name, value in best_program.metrics.items():
            st.write(f"{name}: {value}")
    except Exception as e:
        st.error(str(e))
