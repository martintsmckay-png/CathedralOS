#!/usr/bin/env python3
import os
import re

# Colors for clean terminal reporting in Termux
OK = '\033[92m[✓]\033[0m'
WARN = '\033[93m[!]\033[0m'
ERR = '\033[91m[✕]\033[0m'
INFO = '\033[94m[*]\033[0m'

def inspect_repository():
    print("=" * 50)
    print(" CATHEDRALOS // SYSTEM INTEGRITY AUTOMATION")
    print("=" * 50)

    todo_count = 0
    phantom_count = 0
    completed_quests = 0
    active_quests = 0

    # Target directories to scan
    target_dirs = ['src', 'scripts', 'docs']
    target_files = ['README.md', 'QUESTS.md']

    # 1. Scan files for code anomalies
    for root, dirs, files in os.walk('.'):
        # Skip hidden git folders
        if '.git' in root:
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            
            # Only scan text-based code and doc files
            if file.endswith(('.html', '.css', '.js', '.py', '.cpp', '.md')):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Hunt for Zero-Width Space Phantom (0xE2808B / \u200b)
                        if '\u200b' in content:
                            print(f"{ERR} Phantom Space detected in: {file_path}")
                            phantom_count += 1
                            
                        # Count forgotten TODOs
                        todos = re.findall(r'(?i)//\s*TODO|#\s*TODO', content)
                        if todos:
                            print(f"{WARN} {len(todos)} forgotten comment(s) in: {file_path}")
                            todo_count += len(todos)
                            
                except Exception as e:
                    pass

    # 2. Parse QUESTS.md for architecture progress
    if os.path.exists('QUESTS.md'):
        try:
            with open('QUESTS.md', 'r', encoding='utf-8') as f:
                quests_content = f.read()
                completed_quests = len(re.findall(r'🟢', quests_content))
                active_quests = len(re.findall(r'🟡', quests_content))
        except Exception:
            print(f"{ERR} Failed to parse QUESTS.md")

    # 3. Output Integrity Metrics
    print("\n" + "=" * 50)
    print(" INTEGRITY REPORT SUMMARY")
    print("=" * 50)
    
    if phantom_count == 0:
        print(f"{OK} Zero-Width Phantom Spaces: 0 (Reality Stable)")
    else:
        print(f"{ERR} Total Phantom Spaces Found: {phantom_count}")

    if todo_count == 0:
        print(f"{OK} Forgotten Comments: 0 (The Code has a Voice)")
    else:
        print(f"{WARN} Total Unresolved TODOs: {todo_count}")

    print(f"{INFO} Master Quest Registry: {completed_quests} Completed // {active_quests} Active")
    print("=" * 50)

    # Return clean exit code if no phantoms are breaking reality
    return 0 if phantom_count == 0 else 1

if __name__ == '__main__':
    inspect_repository()

