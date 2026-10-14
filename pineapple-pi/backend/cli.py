import argparse, json
from backend.database import initialize_database
from backend.services.scanner import scan_and_store
from backend.services.preflight import run_preflight

def main() -> None:
    parser=argparse.ArgumentParser(prog="pineapple-pi")
    parser.add_argument("command", choices=["init-db", "scan", "preflight"])
    args=parser.parse_args()
    if args.command == "init-db":
        initialize_database(); print("Database initialized")
    elif args.command == "scan":
        initialize_database(); print(json.dumps(scan_and_store(), indent=2))
    else:
        print(json.dumps(run_preflight(), indent=2))

if __name__ == "__main__": main()
