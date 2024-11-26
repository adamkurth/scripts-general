#!/usr/bin/env python3
"""
Efficient interactive session launcher for SOL supercomputer.
Usage: python interactive.py start [cpu|gpu] <hours>
"""

import subprocess
import sys
import argparse
from datetime import datetime

def get_partition_info():
    """Get partition information using minimal processing"""
    try:
        cmd = ['sinfo', '-h', '-o', '%P %a %l %D %T %N']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Error fetching partition info: {e.stderr}")
        sys.exit(1)

def parse_partition_line(line):
    """Parse a single partition line efficiently"""
    try:
        parts = line.split()
        return {
            'name': parts[0],
            'avail': parts[1],
            'timelimit': parts[2],
            'nodes': int(parts[3]),
            'state': parts[4],
            'nodelist': parts[5] if len(parts) > 5 else ''
        }
    except (IndexError, ValueError):
        return None

def get_available_partitions(resource_type):
    """Get available partitions based on resource type"""
    partitions = []
    partition_data = get_partition_info()
    
    for line in partition_data:
        part = parse_partition_line(line)
        if not part:
            continue
            
        # Filter based on resource type and availability
        is_gpu = 'highmem' in part['name'] or 'htc' in part['name']
        if ((resource_type == 'gpu' and is_gpu) or 
            (resource_type == 'cpu' and not is_gpu)) and part['avail'] == 'up':
            partitions.append(part)
    
    return partitions

def determine_qos(partition_name):
    """Determine QOS based on partition name"""
    if 'htc' in partition_name:
        return 'normal'
    elif 'general' in partition_name:
        return 'public'
    return 'wildfire'

def start_interactive_session(partition, resource_type, hours):
    """Start an interactive session with specified parameters"""
    qos = determine_qos(partition['name'])
    
    # Build command with correct argument order
    cmd = [
        'srun',
        '--partition', partition['name'],
        '--qos', qos,
        '--time', f'{hours}:00:00',
        '--cpus-per-task=1',
        '--pty',
    ]
    
    if resource_type == 'gpu':
        cmd.extend(['--gres=gpu:1'])
    
    # Add shell command at the end
    cmd.append('/bin/bash')
    
    print(f"\nStarting interactive session on partition: {partition['name']}")
    print(f"QOS: {qos}")
    print(f"Time limit: {hours} hours")
    print(f"Resource type: {resource_type}")
    print("\nCommand:", ' '.join(cmd))
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nSession request cancelled by user")
    except subprocess.CalledProcessError as e:
        print(f"\nError starting session: {e}")

def main():
    parser = argparse.ArgumentParser(description='SOL Interactive Session Launcher')
    parser.add_argument('action', choices=['start'], help='Action to perform')
    parser.add_argument('resource_type', choices=['cpu', 'gpu'], help='Resource type')
    parser.add_argument('hours', type=int, help='Session duration in hours')
    
    args = parser.parse_args()
    
    # Get available partitions
    partitions = get_available_partitions(args.resource_type)
    
    if not partitions:
        print(f"No available {args.resource_type} partitions found")
        sys.exit(1)
    
    # Sort partitions by number of available nodes
    partitions.sort(key=lambda x: x['nodes'], reverse=True)
    
    # Display available partitions
    print("\nAvailable partitions:")
    for i, part in enumerate(partitions, 1):
        print(f"{i}. {part['name']} ({part['nodes']} nodes, {part['timelimit']} time limit)")
    
    # Let user select partition
    while True:
        try:
            choice = int(input("\nSelect partition number: ")) - 1
            if 0 <= choice < len(partitions):
                selected_partition = partitions[choice]
                break
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a number.")
    
    # Start session
    start_interactive_session(selected_partition, args.resource_type, args.hours)

if __name__ == "__main__":
    main()