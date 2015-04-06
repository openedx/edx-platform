"""
Initialize the mako template lookup
"""
from django.conf import settings

from edxmako import LOOKUP
from edxmako.paths import add_lookup
from edxmako.startup import run as edxmako_run

from . import TEAMS_NAMESPACE


def run():
    """
    Add the templates directory to the Mako paths
    """
    # Add all of the main directories to the path
    for directory in LOOKUP['main'].directories:
        add_lookup(TEAMS_NAMESPACE, directory)

    # edxmako.paths.add_lookup(TEAMS_NAMESPACE, settings.REPO_ROOT / "lms" / "templates")
    add_lookup(TEAMS_NAMESPACE, settings.REPO_ROOT / "lms" / "djangoapps" / "teams" / "templates")
