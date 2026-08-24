#!/bin/bash
set -e

echo "[*] Initializing C.C.Q. Phase 2 Test Suite..."

TEST_DIR="ccq_p2_sandbox"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Init git repo
git init > /dev/null 2>&1
git config user.name "Steward Test"
git config user.email "steward@cathedral.local"

# Set up local CCQ paths
CCQ_ENGINE="$(pwd)/../ccq_json.py"
mkdir -p bin hooks
cp "../bin/ccq" bin/ 2>/dev/null || cat << 'EOF' > bin/ccq
#!/bin/bash
python3 "$(dirname "$0")/../ccq_json.py" "$@"
EOF
chmod +x bin/ccq
cp "../ccq_json.py" .
cp "../default.json" . 2>/dev/null || cat << 'EOF' > default.json
{"rules": [{"pattern": "rm -rf", "severity": "CRITICAL", "description": "Destructive deletion"}]}
EOF

# Install hook
../bin/ccq-install-hooks --force > /dev/null

echo "[TEST 1] Clean commit pass..."
echo "print('hello world')" > clean.py
git add clean.py
git commit -m "clean commit" > /dev/null 2>&1 && echo "  [PASS] Clean file committed" || (echo "  [FAIL] Clean file blocked"; exit 1)

echo "[TEST 2] Risky file quarantine block..."
echo "rm -rf /" > dangerous.sh
git add dangerous.sh
if git commit -m "dangerous commit" > /dev/null 2>&1; then
    echo "  [FAIL] Quarantine failed to block dangerous file"
    exit 1
else
    echo "  [PASS] Quarantine successfully blocked dangerous file"
fi

echo "[TEST 3] Audit Bypass logging..."
CCQ_BYPASS=1 git commit -m "bypassed commit" > /dev/null 2>&1
python3 ccq_json.py --ledger | grep -q "gate_bypass" && echo "  [PASS] Gate bypass recorded in Lorewraith ledger" || (echo "  [FAIL] Bypass missing from ledger"; exit 1)

echo "[TEST 4] Ledger Integrity..."
python3 ccq_json.py --verify && echo "  [PASS] Full ledger hash chain intact" || (echo "  [FAIL] Hash chain corrupted"; exit 1)

cd ..
rm -rf "$TEST_DIR"
echo "[*] Phase 2 Test Suite Complete — ALL GREEN!"

