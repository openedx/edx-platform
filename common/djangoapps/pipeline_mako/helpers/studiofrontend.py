"""
Contains code that gets run inside our mako template
Debugging python-in-mako is terrible, so we've moved the actual code out to its own file
"""
from django.conf import settings
from django.utils.translation import to_locale


def load_sfe_i18n_messages(language):
    """
    Loads i18n data from studio-frontend's published files.
    """
    messages = "{}"

    if language != 'en':
        # because en is the default, studio-frontend will have it loaded by default
        messages_path = "{base}/studio-frontend/dist/i18n/messages/{locale}.json".format(
            base=settings.STATIC_ROOT_BASE,
            locale=to_locale(language)
        )
        with open(messages_path) as inputfile:
            messages = inputfile.read()

    return messages
