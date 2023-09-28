"""
Lookup list of installed XBlocks, to aid XBlock developers
"""
import pkg_resources


def get_without_builtins():
    """
    Get all installed XBlocks

    but try to omit built-in XBlocks, else the output is less helpful
    """
    xblocks = [
        entry_point.name
        for entry_point in pkg_resources.iter_entry_points('xblock.v1')
        if not entry_point.module_name.startswith('xmodule')
    ]
    xblocks = sorted(xblocks)
    return xblocks


def main():
    """
    Run the main script
    """
    for name in get_without_builtins():
        print(name)


if __name__ == '__main__':
    main()
