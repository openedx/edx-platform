"""Provides management command calling info to tracking context."""

from django.core.management.base import BaseCommand

from eventtracking import tracker


class TrackedCommand(BaseCommand):
    """
    Provides management command calling info to tracking context.

    Information provided to context includes three values:

    'command': the program name and the subcommand used to run a management command.
    'command_args': the argument list passed to the command.
    'command_options': the option dict passed to the command.  This includes options
         that were not explicitly specified, and receive default values.

         Special treatment are provided for several options, including obfuscation and filtering.

         The values for the following options are filtered entirely:
             'settings', 'pythonpath', 'verbosity', 'traceback', 'stdout', 'stderr'.
         The values for the following options are replaced with eight asterisks:
             'password'.

    An example tracking log entry resulting from running the 'create_user' management command:

    {
        "username": "anonymous",
        "host": "",
        "event_source": "server",
        "event_type": "edx.course.enrollment.activated",
        "context": {
            "course_id": "edX/Open_DemoX/edx_demo_course",
            "org_id": "edX",
            "command_options": {
                "username": null,
                "name": null,
                "course": "edX/Open_DemoX/edx_demo_course",
                "mode": "verified",
                "password": "********",
                "email": "rando9c@example.com",
                "staff": false
            },
            "command": "./manage.py create_user",
            "command_args": []
        },
        "time": "2014-01-06T15:59:49.599522+00:00",
        "ip": "",
        "event": {
            "course_id": "edX/Open_DemoX/edx_demo_course",
            "user_id": 29,
            "mode": "verified"
        },
        "agent": "",
        "page": null
    }

    The name of the context used to add (and remove) these values is "edx.mgmt.command".
    The context name is used to allow the context additions to be scoped, but doesn't
    appear in the context itself.
    """
    prog_name = 'unknown'

    def create_parser(self, prog_name, subcommand):
        """Wraps create_parser to snag command line info."""
        self.prog_name = "{} {}".format(prog_name, subcommand)
        return super(TrackedCommand, self).create_parser(prog_name, subcommand)

    def execute(self, *args, **options):
        """Wraps base execute() to add command line to tracking context."""
        # Make a copy of options, and obfuscate or filter particular values.
        options_dict = dict(options)

        # Stuff to obfuscate:
        censored_opts = ['password']
        for opt in censored_opts:
            if opt in options_dict:
                options_dict[opt] = '*' * 8

        # Stuff to filter:
        removed_opts = ['settings', 'pythonpath', 'verbosity', 'traceback', 'stdout', 'stderr']
        for opt in removed_opts:
            if opt in options_dict:
                del options_dict[opt]

        context = {
            'command': self.prog_name,
            'command_args': args,
            'command_options': options_dict,
        }
        COMMAND_CONTEXT_NAME = 'edx.mgmt.command'
        with tracker.get_tracker().context(COMMAND_CONTEXT_NAME, context):
            super(TrackedCommand, self).execute(*args, **options)
