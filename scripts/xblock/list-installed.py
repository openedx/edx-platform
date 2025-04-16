"""
Lookup list of installed XBlocks, to aid XBlock developers
"""
from importlib.metadata import entry_points


def get_without_builtins():
    """
    Get all installed XBlocks

    but try to omit built-in XBlocks, else the output is less helpful
    """
    xblocks = [
        entry_point.name
        for entry_point in entry_points(group='xblock.v1')
        if not entry_point.value.startswith('xmodule')
    ]
    return sorted(xblocks)


def main():
    """
    Run the main script
    """
    for name in get_without_builtins():
        print(name)


if __name__ == '__main__':
    main()
