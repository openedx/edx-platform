"""
Helpers for studio-frontend.

Contains code that gets run inside our mako template
Debugging python-in-mako is terrible, so we've moved the actual code out to its own file
"""


import logging

from django.conf import settings
from django.utils.translation import to_locale

log = logging.getLogger(__name__)


def load_sfe_i18n_messages(language):
    """
    Loads i18n data from studio-frontend's published files.

    This loads the i18n files pulled by the `make pull_translations` command.

    Returns:
        str: unparsed i18n locale JSON file content as a string.
    """
    messages = '{}'

    # because en is the default, studio-frontend will have it loaded by default
    if language != 'en':
        locale = to_locale(language)  # fr-ca --> fr_CA format to match the file name in studio-frontend
        messages_path = settings.REPO_ROOT / 'conf/plugins-locale/studio-frontend' / f'{locale}.json'
        if messages_path.exists():
            try:
                with open(messages_path) as messages_file:
                    messages = messages_file.read()
            except OSError:
                log.error(f"Error loading studiofrontend language files for langauge '{language}'", exc_info=True)
        else:
            log.warning(f"studiofrontend language files for langauge '{language}' was not found.")

    return messages
