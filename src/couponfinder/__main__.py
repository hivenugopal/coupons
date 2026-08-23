"""Allow `python -m couponfinder.admin_api` and `python -m couponfinder`."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
