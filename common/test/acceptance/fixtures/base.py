"""
Base fixtures.
"""
from bok_choy.web_app_fixture import WebAppFixture
from django.core.management import call_command


class DjangoCmdFixture(WebAppFixture):
    """
    Install a fixture by executing a Django management command.
    """

    def __init__(self, cmd, *args, **kwargs):
        """
        Configure the fixture to call `cmd` with the specified
        positional and keyword arguments.
        """
        self._cmd = cmd
        self._args = args
        self._kwargs = kwargs

    def install(self):
        """
        Call the Django management command.
        """
        # We do not catch exceptions here.  Since management commands
        # execute arbitrary Python code, any exception could be raised.
        # So it makes sense to let those go all the way up to the test runner,
        # where they can quickly be found and fixed.
        call_command(self._cmd, *self._args, **self._kwargs)
