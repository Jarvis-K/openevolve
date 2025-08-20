import os
import json
import glob
import logging
import shutil
import re as _re
import time
import threading
from pathlib import Path
from flask import Flask, render_template, render_template_string, jsonify, request


logger = logging.getLogger(__name__)
app = Flask(__name__, template_folder="templates")


def find_latest_checkpoint(base_folder):
    # Check whether the base folder is itself a checkpoint folder
    if os.path.basename(base_folder).startswith("checkpoint_"):
        return base_folder

    checkpoint_folders = glob.glob("**/checkpoint_*", root_dir=base_folder, recursive=True)
    if not checkpoint_folders:
        logger.info(f"No checkpoint folders found in {base_folder}")
        return None
    checkpoint_folders = [os.path.join(base_folder, folder) for folder in checkpoint_folders]
    checkpoint_folders.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    logger.debug(f"Found checkpoint folder: {checkpoint_folders[0]}")
    return checkpoint_folders[0]


def calculate_island_stats(nodes, islands_data, meta):
    """Calculate statistics for each island"""
    stats = []
    island_generations = meta.get("island_generations", [0] * len(islands_data))
    
    for island_idx, island_programs in enumerate(islands_data):
        # Get programs for this island
        island_nodes = [node for node in nodes if node.get("island") == island_idx]
        
        if island_nodes:
            # Calculate scores
            scores = []
            for node in island_nodes:
                metrics = node.get("metrics", {})
                if isinstance(metrics, dict) and "combined_score" in metrics:
                    scores.append(metrics["combined_score"])
            
            best_score = max(scores) if scores else 0.0
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            # Find best program in this island
            best_program = None
            for node in island_nodes:
                metrics = node.get("metrics", {})
                if isinstance(metrics, dict) and metrics.get("combined_score") == best_score:
                    best_program = node
                    break
        else:
            best_score = avg_score = 0.0
            best_program = None
        
        stats.append({
            "island_id": island_idx,
            "population_size": len(island_nodes),
            "best_score": best_score,
            "average_score": avg_score,
            "generation": island_generations[island_idx] if island_idx < len(island_generations) else 0,
            "best_program_id": best_program["id"] if best_program else None,
            "is_current": island_idx == meta.get("current_island", 0)
        })
    
    return stats


def generate_learning_curve(nodes):
    """Generate learning curve data showing best score per iteration"""
    if not nodes:
        return []
    
    # Group programs by iteration and find best score at each iteration
    iteration_best = {}
    
    for node in nodes:
        iteration = node.get("iteration_found", 0)
        metrics = node.get("metrics", {})
        if isinstance(metrics, dict) and "combined_score" in metrics:
            score = metrics["combined_score"]
            if iteration not in iteration_best or score > iteration_best[iteration]["score"]:
                iteration_best[iteration] = {
                    "iteration": iteration,
                    "score": score,
                    "program_id": node["id"],
                    "code": node.get("code", ""),
                    "metrics": metrics
                }
    
    # Convert to sorted list
    learning_curve = list(iteration_best.values())
    learning_curve.sort(key=lambda x: x["iteration"])
    
    # Ensure we have the cumulative best (best score so far)
    cumulative_best = []
    current_best_score = float('-inf')
    
    for point in learning_curve:
        if point["score"] > current_best_score:
            current_best_score = point["score"]
            cumulative_best.append(point)
        else:
            # Use previous best but update iteration
            if cumulative_best:
                prev_best = cumulative_best[-1].copy()
                prev_best["iteration"] = point["iteration"]
                cumulative_best.append(prev_best)
            else:
                cumulative_best.append(point)
    
    return cumulative_best


def load_evolution_data(checkpoint_folder):
    meta_path = os.path.join(checkpoint_folder, "metadata.json")
    programs_dir = os.path.join(checkpoint_folder, "programs")
    if not os.path.exists(meta_path) or not os.path.exists(programs_dir):
        logger.info(f"Missing metadata.json or programs dir in {checkpoint_folder}")
        return {"archive": [], "nodes": [], "edges": [], "checkpoint_dir": checkpoint_folder, "islands_stats": [], "learning_curve": []}
    with open(meta_path) as f:
        meta = json.load(f)

    nodes = []
    id_to_program = {}
    pids = set()
    islands_data = meta.get("islands", [])
    
    for island_idx, id_list in enumerate(islands_data):
        for pid in id_list:
            prog_path = os.path.join(programs_dir, f"{pid}.json")

            # Keep track of PIDs and if one is double, append "-copyN" to the PID
            if pid in pids:
                base_pid = pid

                # If base_pid already has a "-copyN" suffix, strip it
                if "-copy" in base_pid:
                    base_pid = base_pid.rsplit("-copy", 1)[0]

                # Find the next available copy number
                copy_num = 1
                while f"{base_pid}-copy{copy_num}" in pids:
                    copy_num += 1
                pid = f"{base_pid}-copy{copy_num}"
            pids.add(pid)

            if os.path.exists(prog_path):
                with open(prog_path) as pf:
                    prog = json.load(pf)
                prog["id"] = pid
                prog["island"] = island_idx
                nodes.append(prog)
                id_to_program[pid] = prog
            else:
                logger.debug(f"Program file not found: {prog_path}")

    edges = []
    for prog in nodes:
        parent_id = prog.get("parent_id")
        if parent_id and parent_id in id_to_program:
            edges.append({"source": parent_id, "target": prog["id"]})

    # Calculate island statistics
    islands_stats = calculate_island_stats(nodes, islands_data, meta)
    
    # Generate learning curve data (best score per iteration)
    learning_curve = generate_learning_curve(nodes)

    logger.info(f"Loaded {len(nodes)} nodes and {len(edges)} edges from {checkpoint_folder}")
    return {
        "archive": meta.get("archive", []),
        "nodes": nodes,
        "edges": edges,
        "checkpoint_dir": checkpoint_folder,
        "islands_stats": islands_stats,
        "learning_curve": learning_curve,
    }


@app.route("/")
def index():
    return render_template("index.html", checkpoint_dir=checkpoint_dir)


checkpoint_dir = None  # Global variable to store the checkpoint directory
evolution_status = {
    "is_running": False,
    "current_iteration": 0,
    "max_iterations": 0,
    "best_score": None,
    "evolution_speed": 0.0,  # iterations per minute
    "active_programs": 0,
    "success_rate": 0.0,
    "start_time": None,
    "last_update": None,
    "total_programs": 0,
    "failed_programs": 0,
    "score_history": []  # List of (timestamp, score) tuples
}
status_lock = threading.Lock()


@app.route("/api/data")
def data():
    global checkpoint_dir
    base_folder = os.environ.get("EVOLVE_OUTPUT", "examples/circle_packing/")
    checkpoint_dir = find_latest_checkpoint(base_folder)
    if not checkpoint_dir:
        logger.info(f"No checkpoints found in {base_folder}")
        return jsonify({"archive": [], "nodes": [], "edges": [], "checkpoint_dir": ""})

    logger.info(f"Loading data from checkpoint: {checkpoint_dir}")
    data = load_evolution_data(checkpoint_dir)
    
    # Update evolution status based on loaded data
    update_evolution_status_from_data(data)
    
    logger.debug(f"Data: {data}")
    return jsonify(data)


@app.route("/api/status")
def status():
    """Return current evolution status"""
    with status_lock:
        current_status = evolution_status.copy()
        current_status["last_update"] = time.time()
    return jsonify(current_status)


@app.route("/api/status", methods=["POST"])
def update_status():
    """Update evolution status from external source (e.g., controller)"""
    global evolution_status
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        with status_lock:
            # Update provided fields
            for key in ["is_running", "current_iteration", "max_iterations", "best_score", 
                       "active_programs", "success_rate", "total_programs", "failed_programs"]:
                if key in data:
                    evolution_status[key] = data[key]
            
            # Update timestamps
            current_time = time.time()
            evolution_status["last_update"] = current_time
            
            if data.get("is_running") and not evolution_status.get("start_time"):
                evolution_status["start_time"] = current_time
            
            # Update score history
            if "best_score" in data and data["best_score"] is not None:
                score = data["best_score"]
                if not evolution_status["score_history"] or score > evolution_status["score_history"][-1][1]:
                    evolution_status["score_history"].append((current_time, score))
                    # Keep only last 100 entries
                    evolution_status["score_history"] = evolution_status["score_history"][-100:]
            
            # Calculate evolution speed
            if evolution_status["start_time"] and evolution_status["current_iteration"] > 0:
                elapsed_minutes = (current_time - evolution_status["start_time"]) / 60
                if elapsed_minutes > 0:
                    evolution_status["evolution_speed"] = evolution_status["current_iteration"] / elapsed_minutes
        
        return jsonify({"status": "success"})
    
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return jsonify({"error": str(e)}), 500


def update_evolution_status_from_data(data):
    """Update evolution status based on loaded checkpoint data"""
    global evolution_status
    
    with status_lock:
        nodes = data.get("nodes", [])
        if not nodes:
            return
            
        # Calculate current iteration (max iteration found + 1)
        max_iteration = max((node.get("iteration_found", 0) for node in nodes), default=0)
        evolution_status["current_iteration"] = max_iteration
        
        # Find best score
        best_score = None
        for node in nodes:
            metrics = node.get("metrics", {})
            if isinstance(metrics, dict):
                score = metrics.get("combined_score")
                if score is not None and (best_score is None or score > best_score):
                    best_score = score
        
        if best_score is not None:
            evolution_status["best_score"] = best_score
            # Add to score history if it's a new best score
            current_time = time.time()
            if not evolution_status["score_history"] or best_score > evolution_status["score_history"][-1][1]:
                evolution_status["score_history"].append((current_time, best_score))
                # Keep only last 100 entries
                evolution_status["score_history"] = evolution_status["score_history"][-100:]
        
        # Calculate success rate
        total_programs = len(nodes)
        failed_programs = sum(1 for node in nodes if not node.get("metrics"))
        evolution_status["total_programs"] = total_programs
        evolution_status["failed_programs"] = failed_programs
        evolution_status["success_rate"] = (total_programs - failed_programs) / total_programs if total_programs > 0 else 0.0
        
        # Estimate if evolution is running (based on recent activity)
        current_time = time.time()
        if evolution_status["last_update"]:
            time_since_last = current_time - evolution_status["last_update"]
            # Consider running if updated within last 30 seconds
            evolution_status["is_running"] = time_since_last < 30
        else:
            evolution_status["is_running"] = True
            evolution_status["start_time"] = current_time
        
        evolution_status["last_update"] = current_time
        
        # Calculate evolution speed (iterations per minute)
        if evolution_status["start_time"] and max_iteration > 0:
            elapsed_minutes = (current_time - evolution_status["start_time"]) / 60
            if elapsed_minutes > 0:
                evolution_status["evolution_speed"] = max_iteration / elapsed_minutes


@app.route("/program/<program_id>")
def program_page(program_id):
    global checkpoint_dir
    if checkpoint_dir is None:
        return "No checkpoint loaded", 500

    data = load_evolution_data(checkpoint_dir)
    program_data = next((p for p in data["nodes"] if p["id"] == program_id), None)
    program_data = {"code": "", "prompts": {}, **program_data}
    artifacts_json = program_data.get("artifacts_json", None)

    return render_template(
        "program_page.html",
        program_data=program_data,
        checkpoint_dir=checkpoint_dir,
        artifacts_json=artifacts_json,
    )


def run_static_export(args):
    output_dir = args.static_output
    os.makedirs(output_dir, exist_ok=True)

    # Load data and prepare JSON string
    checkpoint_dir = find_latest_checkpoint(args.path)
    if not checkpoint_dir:
        raise RuntimeError(f"No checkpoint found in {args.path}")
    data = load_evolution_data(checkpoint_dir)
    logger.info(f"Exporting visualization for checkpoint: {checkpoint_dir}")

    with app.app_context():
        data_json = jsonify(data).get_data(as_text=True)
    inlined = f"<script>window.STATIC_DATA = {data_json};</script>"

    # Load index.html template
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    template_path = os.path.join(templates_dir, "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Insert static json data into the HTML
    html = _re.sub(r"\{\{\s*url_for\('static', filename='([^']+)'\)\s*\}\}", r"static/\1", html)
    script_tag_idx = html.find('<script type="module"')

    if script_tag_idx != -1:
        html = html[:script_tag_idx] + inlined + "\n" + html[script_tag_idx:]
    else:
        html = html.replace("</body>", inlined + "\n</body>")

    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # Copy over static files
    static_src = os.path.join(os.path.dirname(__file__), "static")
    static_dst = os.path.join(output_dir, "static")
    if os.path.exists(static_dst):
        shutil.rmtree(static_dst)
    shutil.copytree(static_src, static_dst)

    logger.info(
        f"Static export written to {output_dir}/\nNote: This will only work correctly with a web server, not by opening the HTML file directly in a browser. Try $ python3 -m http.server --directory {output_dir} 8080"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OpenEvolve Evolution Visualizer")
    parser.add_argument(
        "--path",
        type=str,
        default="examples/circle_packing/",
        help="Path to openevolve_output or checkpoints folder",
    )
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    parser.add_argument(
        "--static-output",
        type=str,
        default=None,
        help="Produce a static HTML export in this directory and exit.",
    )
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")

    logger.info(f"Current working directory: {os.getcwd()}")

    if args.static_output:
        run_static_export(args)

    os.environ["EVOLVE_OUTPUT"] = args.path
    logger.info(
        f"Starting server at http://{args.host}:{args.port} with log level {args.log_level.upper()}"
    )
    app.run(host=args.host, port=args.port, debug=True)
