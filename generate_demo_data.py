#!/usr/bin/env python3
"""
Generate demo data for testing island and learning curve visualization
"""

import os
import json
import uuid
import random
import math
from pathlib import Path

def generate_demo_program(iteration, island_id, score, parent_id=None):
    """Generate a demo program with realistic code"""
    program_id = str(uuid.uuid4())
    
    # Generate simple Python code that varies by iteration and score
    code_templates = [
        f"""def optimized_function(x):
    # Iteration {iteration}, Island {island_id}
    # Score: {score:.4f}
    result = 0
    for i in range({10 + iteration}):
        result += x * {score:.2f} + {random.uniform(-0.1, 0.1):.3f}
    return result / {10 + iteration}""",
        
        f"""import numpy as np

def evolved_algorithm(data):
    # Generated at iteration {iteration} on island {island_id}
    # Performance score: {score:.4f}
    weights = np.array([{', '.join([f'{random.uniform(0, 1):.3f}' for _ in range(3)])}])
    processed = data * weights.sum() * {score:.3f}
    return processed + {random.uniform(-1, 1):.3f}""",
        
        f"""class OptimizedSolver:
    def __init__(self):
        self.iteration = {iteration}
        self.island = {island_id}
        self.score = {score:.4f}
        self.params = {{{', '.join([f'"{k}": {random.uniform(0, 1):.3f}' for k in ['alpha', 'beta', 'gamma']])}}}
    
    def solve(self, problem):
        return problem * self.params['alpha'] + self.score"""
    ]
    
    code = random.choice(code_templates)
    
    # Generate metrics with some correlation to iteration and randomness
    base_score = score
    metrics = {
        "combined_score": base_score,
        "accuracy": min(1.0, base_score + random.uniform(-0.1, 0.1)),
        "efficiency": min(1.0, base_score * 0.9 + random.uniform(0, 0.2)),
        "complexity": random.uniform(0.3, 0.8),
        "robustness": min(1.0, base_score * 1.1 + random.uniform(-0.15, 0.05))
    }
    
    return {
        "id": program_id,
        "code": code,
        "language": "python",
        "metrics": metrics,
        "iteration_found": iteration,
        "parent_id": parent_id,
        "metadata": {
            "island": island_id,
            "created_at": f"2024-01-{(iteration % 28) + 1:02d}T{(iteration % 24):02d}:00:00Z"
        }
    }

def generate_demo_data(output_dir="demo_evolution_data", num_iterations=50, num_islands=5):
    """Generate complete demo evolution data"""
    
    # Create output directory structure
    checkpoint_dir = Path(output_dir) / "checkpoint_20240115_120000"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    programs_dir = checkpoint_dir / "programs"
    programs_dir.mkdir(exist_ok=True)
    
    print(f"🔧 Generating demo data in {checkpoint_dir}")
    
    # Initialize islands and tracking
    islands = [[] for _ in range(num_islands)]
    all_programs = []
    island_generations = [0] * num_islands
    current_island = 0
    
    # Generate programs across iterations
    for iteration in range(num_iterations):
        # Simulate island switching every few iterations
        if iteration % 10 == 0 and iteration > 0:
            current_island = (current_island + 1) % num_islands
        
        # Generate 1-3 programs per iteration
        num_programs = random.randint(1, 3)
        
        for _ in range(num_programs):
            # Choose island (mostly current, sometimes others for migration)
            if random.random() < 0.8:
                target_island = current_island
            else:
                target_island = random.randint(0, num_islands - 1)
            
            # Calculate score with improvement over time + noise
            base_trend = 0.3 + (iteration / num_iterations) * 0.6  # 0.3 to 0.9
            noise = random.uniform(-0.1, 0.1)
            island_bonus = target_island * 0.02  # Slight island variation
            score = max(0.1, min(0.99, base_trend + noise + island_bonus))
            
            # Occasionally generate breakthrough scores
            if random.random() < 0.05:
                score = min(0.99, score + random.uniform(0.1, 0.3))
            
            # Select parent from same island if available
            parent_id = None
            if islands[target_island] and random.random() < 0.7:
                parent_id = random.choice(islands[target_island])
            
            # Generate program
            program = generate_demo_program(iteration, target_island, score, parent_id)
            
            # Save program to file
            program_file = programs_dir / f"{program['id']}.json"
            with open(program_file, 'w') as f:
                json.dump(program, f, indent=2)
            
            # Track in islands and overall list
            islands[target_island].append(program['id'])
            all_programs.append(program)
            
            # Update island generation
            island_generations[target_island] = max(island_generations[target_island], iteration)
    
    # Generate metadata
    metadata = {
        "version": "1.0",
        "created_at": "2024-01-15T12:00:00Z",
        "num_iterations": num_iterations,
        "num_programs": len(all_programs),
        "islands": [list(island) for island in islands],
        "island_generations": island_generations,
        "current_island": current_island,
        "archive": random.sample([p['id'] for p in all_programs], min(10, len(all_programs))),
        "best_program_id": max(all_programs, key=lambda p: p['metrics']['combined_score'])['id'],
        "config": {
            "num_islands": num_islands,
            "max_iterations": num_iterations
        }
    }
    
    # Save metadata
    metadata_file = checkpoint_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Generated {len(all_programs)} programs across {num_islands} islands")
    print(f"📊 Iterations: {num_iterations}")
    print(f"🏝️  Island populations: {[len(island) for island in islands]}")
    print(f"📈 Best score: {max(p['metrics']['combined_score'] for p in all_programs):.4f}")
    print(f"📁 Data saved to: {checkpoint_dir}")
    
    return str(checkpoint_dir.parent)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate demo evolution data")
    parser.add_argument("--output", type=str, default="demo_evolution_data", help="Output directory")
    parser.add_argument("--iterations", type=int, default=50, help="Number of iterations")
    parser.add_argument("--islands", type=int, default=5, help="Number of islands")
    parser.add_argument("--visualize", action="store_true", help="Start visualizer after generating data")
    
    args = parser.parse_args()
    
    print("🔬 OpenEvolve Demo Data Generator")
    print("=" * 50)
    
    # Generate data
    data_path = generate_demo_data(args.output, args.iterations, args.islands)
    
    if args.visualize:
        print("\n🚀 Starting visualizer...")
        import subprocess
        import sys
        
        try:
            cmd = [
                sys.executable, "scripts/visualizer.py",
                "--path", data_path,
                "--port", "8080"
            ]
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n👋 Visualizer stopped")
        except Exception as e:
            print(f"❌ Error starting visualizer: {e}")
    else:
        print(f"\n🎯 To visualize this data, run:")
        print(f"   python3 scripts/visualizer.py --path {data_path}")
        print(f"   or")
        print(f"   python3 test_island_viz.py --path {data_path}")