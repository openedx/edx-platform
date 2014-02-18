"""
Function to check debug status.
"""
import os

def should_show_debug_toolbar(request):
    """
    Return True/False to determine whether to show the Django
    Debug Toolbar.

    If HIDE_TOOLBAR is set in the process environment, the
    toolbar will be hidden.
    """
    return not bool(os.getenv('HIDE_TOOLBAR', ''))
