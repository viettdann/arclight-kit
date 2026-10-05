import os


def option(key, default):
    return os.environ.get(f"ARC_{key.upper()}", "").strip() or default
