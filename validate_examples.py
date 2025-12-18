#!/usr/bin/env python3
"""
Script to validate all Goal DSL model files in the examples directory.
Runs 'goaldsl validate <goalDSL_model_file>' on each .goal file found.
"""

import os
import subprocess
import sys
from pathlib import Path

def find_goal_files(examples_dir):
    """Find all .goal files in the examples directory recursively."""
    goal_files = []
    for root, dirs, files in os.walk(examples_dir):
        for file in files:
            if file.endswith('.goal'):
                goal_files.append(os.path.join(root, file))
    return sorted(goal_files)

def validate_file(goal_file):
    """Validate a single Goal DSL model file."""
    try:
        result = subprocess.run(
            ['goaldsl', 'validate', goal_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Timeout validating {goal_file}"
    except FileNotFoundError:
        return False, "", "Error: 'goaldsl' command not found. Make sure it's installed and in PATH."
    except Exception as e:
        return False, "", str(e)

def main():
    # Get the examples directory
    examples_dir = './examples/'
    
    if not os.path.exists(examples_dir):
        print(f"Error: Examples directory not found at {examples_dir}")
        sys.exit(1)
    
    # Find all Goal DSL files
    goal_files = find_goal_files(examples_dir)
    
    if not goal_files:
        print(f"No .goal files found in {examples_dir}")
        sys.exit(1)
    
    print(f"Found {len(goal_files)} Goal DSL model files to validate.\n")
    
    # Validate each file
    passed = 0
    failed = 0
    failures = []
    
    for goal_file in goal_files:
        # Make path relative for better readability
        rel_path = os.path.relpath(goal_file, examples_dir)
        print(f"Validating: {rel_path}...", end=" ", flush=True)
        
        success, stdout, stderr = validate_file(goal_file)
        
        if success:
            print("✓ PASSED")
            passed += 1
        else:
            print("✗ FAILED")
            failed += 1
            failures.append({
                'file': rel_path,
                'stdout': stdout,
                'stderr': stderr
            })
    
    # Print summary
    print(f"\n{'='*70}")
    print("Validation Summary:")
    print(f"  Total:  {len(goal_files)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"{'='*70}")
    
    # Print failures if any
    if failures:
        print("\nFailure Details:\n")
        for failure in failures:
            print(f"File: {failure['file']}")
            if failure['stderr']:
                print(f"Error:\n{failure['stderr']}")
            if failure['stdout']:
                print(f"Output:\n{failure['stdout']}")
            print("-" * 70)
        sys.exit(1)
    else:
        print("\nAll validations passed! ✓")
        sys.exit(0)

if __name__ == '__main__':
    main()
