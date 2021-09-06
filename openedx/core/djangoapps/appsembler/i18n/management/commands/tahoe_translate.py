"""
Command to test Tahoe `gettext` without the need to use the GUI.
"""

from django.core.management.base import BaseCommand
from openedx.core.djangoapps.appsembler.i18n.helpers import translate, xblock_translate


class Command(BaseCommand):
    """
    Test Tahoe `gettext` without the need to use the GUI with xblock support.

    Currently missing the following features:
      1) TODO: Handle theme translations
      2) TODO: Support JavaScript edX Platform translations (djangojs.po)
      3) TODO: Support JavaScript XBlock translations (textjs.po)
    """

    help = "Test Tahoe `gettext` without the need to use the GUI with xblock support."

    def add_arguments(self, parser):
        parser.add_argument(
            '-x', '--xblock',
            default=None,
            help='A name for the XBlock to use the translations for.'
        )
        parser.add_argument(
            'language',
            help='The language code to translate to e.g. "eo", "ja-jp", "fr-ca".'
        )
        parser.add_argument(
            'text',
            help='The text to translate. Always provide the English text in quotes e.g. "Sign in".',
        )

    def handle(self, *args, **options):
        translated_text = translate(options['language'], options['text'])

        if options['xblock']:
            translated_xblock_text = xblock_translate(options['xblock'], options['language'], options['text'])
        else:
            translated_xblock_text = ''

        self.stdout.write(
            'Translation result: \n'
            '  - Source language:         en\n'
            '  - Translation language:    {lang}\n'
            '  - Source text:             "{text}" (stripped)\n'
            '  - Translated text:         "{translated_text}" (stripped)\n'
            '\n'
            '  - XBlock:                  {xblock}\n'
            '  - XBlock translated text : "{translated_xblock_text}" (stripped)\n'
            '\n'.format(
                lang=options['language'],
                text=options['text'].strip(),
                xblock=options['xblock'] or '[Not used]',
                translated_text=translated_text.strip(),
                translated_xblock_text=translated_xblock_text.strip() if translated_xblock_text else '',
            )
        )
