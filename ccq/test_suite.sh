#!/usr/bin/env bash

# ==============================================================================
# C.C.Q. (Cathedral Customs & Quarantine) - Phase 1 Test Suite
# Tests immutable ledger, policy engine, and the Refugee Protocol.
# ==============================================================================

# Terminal Colors for Termux
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}[*] Initializing C.C.Q. Phase 1 Test Suite...${NC}"

# Setup Test Environment
mkdir -p ccq_test_sandbox
cd ccq_test_sandbox
export CCQ_LEDGER="test_ledger.json"
rm -f $CCQ_LEDGER # Start clean

# Helper function for pass/fail output
assert_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[PASS]${NC} $1"
    else
        echo -e "${RED}[FAIL]${NC} $1"
    fi
}

assert_fail() {
    if [ $? -ne 0 ]; then
        echo -e "${GREEN}[PASS]${NC} $1"
    else
        echo -e "${RED}[FAIL]${NC} $1 (Expected failure but it succeeded)"
    fi
}

# ==============================================================================
# 🧪 THE 8 TEST CASES
# ==============================================================================

# Test 1: Character Escaping (Handling weird filenames)
echo "bad filename \"with' quotes.txt" > "weird_name.txt"
../bin/ccq --inspect "weird_name.txt" > /dev/null 2>&1
assert_success "Test 1: Character Escaping in JSON payload"

# Test 2: Sequential Chaining (Appending to ledger securely)
echo "safe file 1" > safe1.txt
echo "safe file 2" > safe2.txt
../bin/ccq --inspect safe1.txt > /dev/null 2>&1
../bin/ccq --inspect safe2.txt > /dev/null 2>&1
assert_success "Test 2: Sequential Chaining & backward linking"

# Test 3: Tamper Detection (Simulating an attack on the ledger)
sed -i 's/safe1.txt/hacked.txt/' $CCQ_LEDGER 2>/dev/null
../bin/ccq --verify > /dev/null 2>&1
assert_fail "Test 3: Tamper Detection (Verify caught the hash mismatch)"

# Reset Ledger for remaining tests
rm -f $CCQ_LEDGER

# Test 4: Structured Finding Extraction (Catching dangerous commands)
echo "system('rm -rf /');" > dangerous_code.cpp
../bin/ccq --inspect dangerous_code.cpp | grep -q "SEVERITY"
assert_success "Test 4: Structured Finding Extraction (Policy hit on rm -rf)"

# Test 5: Refugee Protocol Handling (Untracked files)
echo "stateless data" > lost_artifact.dat
../bin/ccq --inspect lost_artifact.dat > /dev/null 2>&1
grep -q "stateless_artifact" $CCQ_LEDGER
assert_success "Test 5: Refugee Protocol classification applied"

# Test 6: Custom Policy Loading
echo '{"rules": [{"pattern": "BANANA", "severity": "HIGH", "description": "No bananas allowed"}]}' > custom_policy.json
echo "I like BANANA" > fruit.txt
../bin/ccq --policy custom_policy.json --inspect fruit.txt | grep -q "No bananas allowed"
assert_success "Test 6: Custom Policy Loading executed"

# Test 7: Steward Gate Approval
# Simulating a steward approving a flagged record
RECORD_ID=$(grep -o '"id": "[^"]*' $CCQ_LEDGER | head -n 1 | cut -d'"' -f4)
../bin/ccq --approve "$RECORD_ID" > /dev/null 2>&1
assert_success "Test 7: Steward Gate log approval"

# Test 8: Full Chain Integrity Verification
../bin/ccq --verify > /dev/null 2>&1
assert_success "Test 8: Full Immutable Ledger Hash Verification"

# ==============================================================================
# Cleanup
# ==============================================================================
cd ..
rm -rf ccq_test_sandbox
echo -e "${BLUE}[*] Test Suite Complete!${NC}"

