"""
Helper functions for constructing shell commands.
"""


def cmd(*args):
    """
    Concatenate the arguments into a space-separated shell command.
    """
    return " ".join(str(arg) for arg in args if arg)


def django_cmd(sys, settings, *args):
    """
    Construct a Django management command.

    `sys` is either 'lms' or 'studio'.
    `settings` is the Django settings module (such as "dev" or "test")
    `args` are concatenated to form the rest of the command.
    """
    # Maintain backwards compatibility with manage.py,
    # which calls "studio" "cms"
    sys = 'cms' if sys == 'studio' else sys
    return cmd("python manage.py", sys, f"--settings={settings}", *args)
