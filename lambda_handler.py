import os
from typing import Any, Dict
from main import run_once


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # Always run a full cycle (no dry-run, fetch from both sources)
    run_once()
    return {"status": "ok"}


if __name__ == "__main__":
    out = handler({}, None)
    print(out)
