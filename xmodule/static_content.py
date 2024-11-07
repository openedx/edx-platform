# /usr/bin/env python
"""
This module used to hold a CLI utility for gathering up the JS and Sass used by several built-in XBlocks.

It now remains as a stub, just for backwards compatibility.

It will soon be removed as part of https://github.com/openedx/edx-platform/issues/31798.
"""
import logging
import sys


def main():
    """
    Warn that this script is now a stub, and return success (zero).
    """
    logging.warning(
        "xmodule/static_content.py, aka xmodule_assets, is now a no-op. "
        "Please remove calls to it from your build pipeline. It will soon be deleted.",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
