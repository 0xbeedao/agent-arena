#!/usr/bin/env python3
import os
import sys

if len(sys.argv) != 2:
    print("Usage: python resort.py <directory>")
    sys.exit(1)

directory = sys.argv[1]

# Get all .bru files in the directory (non-recursive)
bru_files = [f for f in os.listdir(directory) if f.endswith('.bru')]

# Sort alphabetically by name
sorted_files = sorted(bru_files)

# Process each file in the sorted list
for index, filename in enumerate(sorted_files, start=1):
    file_path = os.path.join(directory, filename)
    
    # Read the file content
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Process each line
    new_lines = []
    for line in lines:
        if line.startswith('  seq: '):
            new_lines.append(f'  seq: {index}\n')
        else:
            new_lines.append(line)
    
    # Write back to the file
    with open(file_path, 'w') as f:
        f.writelines(new_lines)