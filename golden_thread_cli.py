from pathlib import Path
from golden_thread import seal_ledger_file


def seal_all_quarantine_ledgers(quarantine_dir="ccq_quarantine"):
    root = Path(quarantine_dir)

    if not root.exists():
        print(f"[ERROR] Quarantine directory not found: {root}")
        return 1

    sealed = 0
    failed = 0

    for ledger_file in sorted(root.glob("*/ledger.json")):
        try:
            digest = seal_ledger_file(ledger_file)
            print(f"[SEALED] {ledger_file} -> {digest}")
            sealed += 1
        except Exception as exc:
            print(f"[FAILED] {ledger_file}: {exc}")
            failed += 1

    print(f"[GOLDEN_THREAD_COMPLETE] sealed={sealed} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(seal_all_quarantine_ledgers())
