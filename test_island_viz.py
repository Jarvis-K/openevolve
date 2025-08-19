#!/usr/bin/env python3
"""
Test script to demonstrate the new island and learning curve visualization features
"""

import os
import sys
import argparse
import subprocess
import time

def run_visualizer(path="examples/circle_packing/", port=8080):
    """Run the visualizer with island and learning curve features"""
    print("🚀 Starting OpenEvolve Visualizer with Island & Learning Curve Features")
    print(f"📊 Data path: {path}")
    print(f"🌐 Server will be available at: http://localhost:{port}")
    print()
    print("New features available:")
    print("  📊 Islands Tab - View status of each evolution island")
    print("  📈 Learning Curve Tab - Interactive learning curve with code viewer")
    print("  🎯 Click on learning curve points to view corresponding code")
    print()
    
    # Set environment variable
    os.environ["EVOLVE_OUTPUT"] = path
    
    try:
        # Run the visualizer
        cmd = [
            sys.executable, "scripts/visualizer.py",
            "--path", path,
            "--port", str(port),
            "--log-level", "INFO"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        print("Press Ctrl+C to stop the server")
        print("="*60)
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down visualizer...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running visualizer: {e}")
        return 1
    except FileNotFoundError:
        print("❌ Error: visualizer.py not found. Make sure you're in the project root directory.")
        return 1
    
    return 0

def check_example_data(path):
    """Check if example data exists"""
    if not os.path.exists(path):
        print(f"⚠️  Warning: Path {path} does not exist")
        print("   You may need to run an evolution experiment first to generate data.")
        return False
    
    # Look for checkpoint folders
    checkpoint_found = False
    if os.path.isdir(path):
        for item in os.listdir(path):
            if item.startswith("checkpoint_"):
                checkpoint_found = True
                break
    
    if not checkpoint_found:
        print(f"⚠️  Warning: No checkpoint folders found in {path}")
        print("   The visualizer may not have data to display.")
        return False
    
    print(f"✅ Found evolution data in {path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test OpenEvolve Island & Learning Curve Visualization")
    parser.add_argument(
        "--path", 
        type=str, 
        default="examples/circle_packing/",
        help="Path to evolution data (default: examples/circle_packing/)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080,
        help="Port to run the server on (default: 8080)"
    )
    parser.add_argument(
        "--check-only", 
        action="store_true",
        help="Only check for data availability, don't start server"
    )
    
    args = parser.parse_args()
    
    print("🔬 OpenEvolve Island & Learning Curve Visualization Test")
    print("="*60)
    
    # Check if data exists
    data_available = check_example_data(args.path)
    
    if args.check_only:
        if data_available:
            print("✅ Data check passed - ready to visualize!")
            sys.exit(0)
        else:
            print("❌ Data check failed - no visualization data found")
            sys.exit(1)
    
    if not data_available:
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting...")
            sys.exit(1)
    
    print()
    sys.exit(run_visualizer(args.path, args.port))