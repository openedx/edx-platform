"""
Monkey patch implementation to not throw errors when directories don't exist
Currently in 1.9.5 but not 1.8
https://github.com/django/django/pull/4262/files
https://code.djangoproject.com/ticket/23986
"""

from django.contrib.staticfiles.management.commands.collectstatic import Command


def patch():
    """
    Monkey-patch the static files management command
    """
    def create_collectstatic_wrapper(wrapped_func):
        # pylint: disable=missing-docstring
        wrapped_func = wrapped_func.__func__

        def _clear_dir(self, path, **kwargs):
            # Django has a bug when you collecstatic --clean and directories don't exist
            # This happens if those files are gitignored, and cleaning really shouldn't die
            # when the directory it wants to remove is already gone.
            if not self.storage.exists(path):
                return
            else:
                return wrapped_func(self, path, **kwargs)
        return _clear_dir

    Command.clear_dir = create_collectstatic_wrapper(Command.clear_dir)
