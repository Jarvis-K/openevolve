#!/usr/bin/env python3
"""
Test the data processing logic for islands and learning curve without Flask dependencies
"""

import os
import json
import sys
from pathlib import Path

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
    """Load and process evolution data"""
    meta_path = os.path.join(checkpoint_folder, "metadata.json")
    programs_dir = os.path.join(checkpoint_folder, "programs")
    
    if not os.path.exists(meta_path) or not os.path.exists(programs_dir):
        print(f"❌ Missing metadata.json or programs dir in {checkpoint_folder}")
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
                if "-copy" in base_pid:
                    base_pid = base_pid.rsplit("-copy", 1)[0]
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

    edges = []
    for prog in nodes:
        parent_id = prog.get("parent_id")
        if parent_id and parent_id in id_to_program:
            edges.append({"source": parent_id, "target": prog["id"]})

    # Calculate island statistics
    islands_stats = calculate_island_stats(nodes, islands_data, meta)
    
    # Generate learning curve data (best score per iteration)
    learning_curve = generate_learning_curve(nodes)

    print(f"✅ Loaded {len(nodes)} nodes and {len(edges)} edges from {checkpoint_folder}")
    return {
        "archive": meta.get("archive", []),
        "nodes": nodes,
        "edges": edges,
        "checkpoint_dir": checkpoint_folder,
        "islands_stats": islands_stats,
        "learning_curve": learning_curve,
    }


def test_data_processing(data_path):
    """Test the data processing functionality"""
    print("🔬 Testing Island & Learning Curve Data Processing")
    print("=" * 60)
    
    # Find checkpoint folder
    checkpoint_folder = None
    if os.path.isdir(data_path):
        for item in os.listdir(data_path):
            if item.startswith("checkpoint_"):
                checkpoint_folder = os.path.join(data_path, item)
                break
    
    if not checkpoint_folder:
        print(f"❌ No checkpoint folder found in {data_path}")
        return False
    
    print(f"📁 Using checkpoint: {checkpoint_folder}")
    
    # Load and process data
    try:
        data = load_evolution_data(checkpoint_folder)
        
        # Test islands stats
        islands_stats = data['islands_stats']
        print(f"\n🏝️  Islands Statistics:")
        print(f"   Number of islands: {len(islands_stats)}")
        
        for i, island in enumerate(islands_stats):
            current_marker = " *" if island['is_current'] else "  "
            print(f"{current_marker} Island {island['island_id']}: "
                  f"{island['population_size']} programs, "
                  f"best={island['best_score']:.4f}, "
                  f"avg={island['average_score']:.4f}, "
                  f"gen={island['generation']}")
        
        # Test learning curve
        learning_curve = data['learning_curve']
        print(f"\n📈 Learning Curve:")
        print(f"   Number of data points: {len(learning_curve)}")
        
        if learning_curve:
            print(f"   First point: iteration {learning_curve[0]['iteration']}, score {learning_curve[0]['score']:.4f}")
            print(f"   Last point: iteration {learning_curve[-1]['iteration']}, score {learning_curve[-1]['score']:.4f}")
            print(f"   Best score: {max(point['score'] for point in learning_curve):.4f}")
            
            # Show a few sample points
            print(f"\n   Sample learning curve points:")
            for i, point in enumerate(learning_curve[:5]):
                print(f"     {i+1}. Iter {point['iteration']:2d}: {point['score']:.4f} (Program: {point['program_id'][:8]}...)")
            
            if len(learning_curve) > 5:
                print(f"     ... and {len(learning_curve) - 5} more points")
        
        # Test code content
        if learning_curve and learning_curve[0].get('code'):
            print(f"\n💻 Sample Code (from iteration {learning_curve[0]['iteration']}):")
            code_lines = learning_curve[0]['code'].split('\n')[:5]
            for line in code_lines:
                print(f"     {line}")
            if len(learning_curve[0]['code'].split('\n')) > 5:
                print("     ...")
        
        print(f"\n✅ Data processing test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test island and learning curve data processing")
    parser.add_argument("--path", type=str, default="demo_evolution_data", help="Path to evolution data")
    
    args = parser.parse_args()
    
    success = test_data_processing(args.path)
    sys.exit(0 if success else 1)