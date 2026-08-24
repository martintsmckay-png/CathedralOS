#!/usr/bin/env python3
import sys
import os
import json
import hashlib
import re
import uuid
import subprocess
from datetime import datetime, timezone

def compute_record_hash(record):
    rec_copy = {k: v for k, v in record.items() if k != "record_hash"}
    canonical_str = json.dumps(rec_copy, sort_keys=True)
    return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

def load_ledger(ledger_file):
    if os.path.exists(ledger_file):
        try:
            with open(ledger_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_ledger(ledger_file, ledger):
    with open(ledger_file, 'w', encoding='utf-8') as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)

def verify_ledger(ledger_file):
    ledger = load_ledger(ledger_file)
    if not ledger:
        return True
    
    prev_hash = None
    for idx, record in enumerate(ledger):
        actual_hash = record.get("record_hash")
        calculated_hash = compute_record_hash(record)
        
        if actual_hash != calculated_hash or record.get("previous_record_hash") != prev_hash:
            return False
            
        prev_hash = actual_hash
    return True

def get_staged_content(filepath):
    try:
        res = subprocess.run(["git", "show", f":{filepath}"], capture_output=True, text=True, check=True)
        return res.stdout
    except Exception:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        return ""

def inspect_content(content, target_name, policy_path="default.json", ledger_file="test_ledger.json"):
    if policy_path == "default.json" and not os.path.exists(policy_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fallback_path = os.path.join(script_dir, "default.json")
        if os.path.exists(fallback_path):
            policy_path = fallback_path

    rules = []
    if os.path.exists(policy_path):
        try:
            with open(policy_path, 'r', encoding='utf-8') as f:
                pdata = json.load(f)
                rules = pdata.get("rules", [])
        except Exception:
            rules = []

    findings = []
    for rule in rules:
        pattern = rule.get("pattern", "")
        if pattern and re.search(pattern, content):
            findings.append({
                "pattern": pattern,
                "severity": rule.get("severity", "UNKNOWN"),
                "description": rule.get("description", "Policy rule hit")
            })

    ledger = load_ledger(ledger_file)
    prev_hash = ledger[-1]["record_hash"] if ledger else None
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    record = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": target_name,
        "content_hash": content_hash,
        "status": "REVIEW" if findings else "CLEAN",
        "findings": findings,
        "previous_record_hash": prev_hash
    }

    record["record_hash"] = compute_record_hash(record)
    ledger.append(record)
    save_ledger(ledger_file, ledger)

    return record

def approve_record(record_id, ledger_file="test_ledger.json"):
    ledger = load_ledger(ledger_file)
    updated = False
    for idx, record in enumerate(ledger):
        if record.get("id") == record_id:
            record["status"] = "APPROVED"
            updated = True
            for j in range(idx, len(ledger)):
                if j > 0:
                    ledger[j]["previous_record_hash"] = ledger[j-1]["record_hash"]
                ledger[j]["record_hash"] = compute_record_hash(ledger[j])
            break
    if updated:
        save_ledger(ledger_file, ledger)
        print(f"Record {record_id} approved.")
    else:
        print(f"Record {record_id} not found.")

def check_approval(filepath, ledger_file="test_ledger.json"):
    content = get_staged_content(filepath)
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    ledger = load_ledger(ledger_file)
    
    for record in reversed(ledger):
        if record.get("target") == filepath and record.get("content_hash") == content_hash:
            if record.get("status") == "APPROVED":
                return True
    return False

def record_bypass(reason, ledger_file="test_ledger.json"):
    ledger = load_ledger(ledger_file)
    prev_hash = ledger[-1]["record_hash"] if ledger else None
    
    record = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "gate_bypass",
        "reason": reason,
        "previous_record_hash": prev_hash
    }
    record["record_hash"] = compute_record_hash(record)
    ledger.append(record)
    save_ledger(ledger_file, ledger)
    print(f"Bypass logged: {reason}")

def main():
    ledger_file = os.environ.get("CCQ_LEDGER", "test_ledger.json")
    policy_path = os.environ.get("CCQ_POLICY", "default.json")

    args = sys.argv[1:]
    if not args:
        sys.exit(1)

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--policy":
            policy_path = args[i+1]
            i += 2
        elif arg == "--inspect":
            target = args[i+1]
            content = get_staged_content(target)
            rec = inspect_content(content, target, policy_path=policy_path, ledger_file=ledger_file)
            if rec["status"] == "REVIEW":
                print(f"FINDINGS DETECTED for {target}")
            i += 2
        elif arg == "--staged":
            try:
                res = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], capture_output=True, text=True, check=True)
                staged_files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
            except Exception:
                staged_files = []

            has_unapproved_findings = False
            for f in staged_files:
                content = get_staged_content(f)
                rec = inspect_content(content, f, policy_path=policy_path, ledger_file=ledger_file)
                if rec["status"] == "REVIEW":
                    if not check_approval(f, ledger_file=ledger_file):
                        print(f"[C.C.Q. QUARANTINE] Staged file '{f}' failed inspection.")
                        has_unapproved_findings = True

            if has_unapproved_findings:
                sys.exit(1)
            i += 1
        elif arg == "--check-approval":
            target = args[i+1]
            approved = check_approval(target, ledger_file=ledger_file)
            sys.exit(0 if approved else 1)
        elif arg == "--bypass":
            reason = args[i+1] if i+1 < len(args) else "No reason provided"
            record_bypass(reason, ledger_file=ledger_file)
            i += 2
        elif arg == "--verify":
            valid = verify_ledger(ledger_file)
            sys.exit(0 if valid else 1)
        elif arg == "--approve":
            rec_id = args[i+1]
            approve_record(rec_id, ledger_file=ledger_file)
            i += 2
        elif arg == "--ledger":
            ledger = load_ledger(ledger_file)
            print(json.dumps(ledger, indent=2))
            i += 1
        else:
            i += 1

if __name__ == "__main__":
    main()

