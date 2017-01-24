import json
from StringIO import StringIO
from django.test import TestCase

from eventtracking import tracker as eventtracker

from track.management.tracked_command import TrackedCommand


class DummyCommand(TrackedCommand):
    """A locally-defined command, for testing, that returns the current context as a JSON string."""
    def handle(self, *args, **options):
        return json.dumps(eventtracker.get_tracker().resolve_context())


class CommandsTestBase(TestCase):

    def _run_dummy_command(self, *args, **kwargs):
        """Runs the test command's execute method directly, and outputs a dict of the current context."""
        out = StringIO()
        DummyCommand().execute(*args, stdout=out, **kwargs)
        out.seek(0)
        return json.loads(out.read())

    def test_command(self):
        args = ['whee']
        kwargs = {'key1': 'default', 'key2': True}
        json_out = self._run_dummy_command(*args, **kwargs)
        self.assertEquals(json_out['command'], 'unknown')
