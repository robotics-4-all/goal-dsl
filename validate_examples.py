#!/usr/bin/env python

import os
import subprocess

examples_dir = './examples/'
total_successes = 0
total_failures = 0

for subdir in os.listdir(examples_dir):
    subdir_path = os.path.join(examples_dir, subdir)
    if os.path.isdir(subdir_path):
        print(f"\n{'=' * 50}")
        print(f"Processing: {subdir.upper()}")
        print(f"{'=' * 50}")
        goal_files = [f for f in os.listdir(subdir_path) if f.endswith('.goal')]
        successes = 0
        failures = 0
        for goal_file in goal_files:
            file_path = os.path.join(subdir_path, goal_file)
            print(f"\n{'-' * 40}")
            print(f"Validating: {goal_file}")
            print(f"{'-' * 40}")
            command = f"goaldsl validate {file_path}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            print(result.stdout.strip())
            if result.returncode == 0:
                successes += 1
            else:
                failures += 1
                print(f"\n{'!' * 40}")
                print(f"Error in {subdir}:")
                print(f"{'!' * 40}")
                print(result.stderr.strip())

        total_successes += successes
        total_failures += failures

        print(f"\n{'#' * 50}")
        print(f"Results for {subdir.upper()}:")
        print(f"Successes: {successes}")
        print(f"Failures: {failures}")
        print(f"{'#' * 50}")

print("\nFinal Results:")
print(f"{'*' * 50}")
print(f"Total Successes: {total_successes}")
print(f"Total Failures: {total_failures}")
print(f"{'*' * 50}")
