import argparse


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="notes", description="Sync notes to the server.")
    p.add_argument("--server", default="https://notes.acme.internal")
    p.add_argument("--verbose", action="store_true", help="print every request")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.verbose:
        print(f"syncing to {args.server}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
