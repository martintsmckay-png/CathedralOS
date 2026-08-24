import hashlib
import json
from datetime import datetime, timezone

class VoyagerLedgerEntry:
    def __init__(self, event_type, artifact_hash, steward_id, payload, previous_hash=None):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.event_type = event_type
        self.artifact_hash = artifact_hash
        self.steward_id = steward_id
        self.payload = payload
        self.previous_hash = previous_hash
        self.record_hash = self.calculate_hash()

    def calculate_hash(self):
        entry_dict = {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "artifact_hash": self.artifact_hash,
            "steward_id": self.steward_id,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
        }
        canonical_json = json.dumps(entry_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

class VoyagerAuditChain:
    def __init__(self):
        self.chain = []

    def append_event(self, event_type, artifact_hash, steward_id, payload):
        previous_hash = self.chain[-1].record_hash if self.chain else None
        entry = VoyagerLedgerEntry(event_type, artifact_hash, steward_id, payload, previous_hash)
        self.chain.append(entry)
        return entry

    def verify_chain(self):
        for i in range(len(self.chain)):
            current = self.chain[i]
            if current.record_hash != current.calculate_hash():
                return False, f"Integrity check failed at index {i}"
            if i > 0 and current.previous_hash != self.chain[i - 1].record_hash:
                return False, f"Chain break at index {i}"
        return True, "Chain intact. Evidence verified."

# Run test sequence
if __name__ == "__main__":
    ledger = VoyagerAuditChain()
    artifact = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    ledger.append_event("INSPECTION", artifact, "auditor-01", {"findings": ["Resonance drift"]})
    ledger.append_event("DECISION", artifact, "steward-martin", {"decision": "GROUND_SYSTEM"})
    ledger.append_event("APPROVAL", artifact, "lead-steward", {"status": "APPROVED"})
    
    valid, status = ledger.verify_chain()
    print(f"Ledger Status: {status}")
    print(f"Total Entries: {len(ledger.chain)}")
    print(f"Latest Record Hash: {ledger.chain[-1].record_hash}")
