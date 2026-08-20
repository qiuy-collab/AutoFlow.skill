#!/usr/bin/env python3
"""Check local availability of the nature-figure package.

Output (JSON on stdout): {"status": "available"|"missing"|"blocked", "version": ...}
"""
import json
import sys


def main() -> int:
    missing_deps = []
    versions = []
    for module, name in (("numpy", "numpy"), ("matplotlib", "matplotlib")):
        try:
            mod = __import__(module)
            versions.append(f"{name}={getattr(mod, '__version__', 'unknown')}")
        except ImportError:
            missing_deps.append(name)
    if missing_deps:
        print(json.dumps({"status": "missing", "version": None, "error": f"Missing Python deps: {', '.join(missing_deps)}"}))
        return 0
    print(json.dumps({"status": "available", "version": ", ".join(versions)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
