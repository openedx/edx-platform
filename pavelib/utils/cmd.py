"""
Helper functions for constructing shell commands.
"""


def cmd(*args):
    """
    Concatenate the arguments into a space-separated shell command.
    """
    return " ".join(str(arg) for arg in args if arg)
