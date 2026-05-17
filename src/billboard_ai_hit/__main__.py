from __future__ import annotations

import sys

from .hook_demo import main as hook_demo_main
from .pipeline import main as pipeline_main


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "hook-demo":
        return hook_demo_main(args[1:])
    if args and args[0] == "pipeline":
        return pipeline_main(args[1:])
    return pipeline_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
