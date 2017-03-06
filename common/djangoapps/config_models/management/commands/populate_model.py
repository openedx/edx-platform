"""
Populates a ConfigurationModel by deserializing JSON data contained in a file.
"""
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _

from config_models.utils import deserialize_json


class Command(BaseCommand):
    """
    This command will deserialize the JSON data in the supplied file to populate
    a ConfigurationModel. Note that this will add new entries to the model, but it
    will not delete any entries (ConfigurationModel entries are read-only).
    """
    help = """
    Populates a ConfigurationModel by deserializing the supplied JSON.

    JSON should be in a file, with the following format:

    { "model": "config_models.ExampleConfigurationModel",
      "data":
        [
          { "enabled": True,
            "color": "black"
            ...
          },
          { "enabled": False,
            "color": "yellow"
            ...
          },
          ...
        ]
    }

    A username corresponding to an existing user must be specified to indicate who
    is executing the command.

        $ ... populate_model -f path/to/file.json -u username
    """

    option_list = BaseCommand.option_list + (
        make_option('-f', '--file',
                    metavar='JSON_FILE',
                    dest='file',
                    default=False,
                    help='JSON file to import ConfigurationModel data'),
        make_option('-u', '--username',
                    metavar='USERNAME',
                    dest='username',
                    default=False,
                    help='username to specify who is executing the command'),
    )

    def handle(self, *args, **options):
        if 'file' not in options or not options['file']:
            raise CommandError(_("A file containing JSON must be specified."))

        if 'username' not in options or not options['username']:
            raise CommandError(_("A valid username must be specified."))

        json_file = options['file']
        if not os.path.exists(json_file):
            raise CommandError(_("File {0} does not exist").format(json_file))

        self.stdout.write(_("Importing JSON data from file {0}").format(json_file))
        with open(json_file) as data:
            created_entries = deserialize_json(data, options['username'])
            self.stdout.write(_("Import complete, {0} new entries created").format(created_entries))
