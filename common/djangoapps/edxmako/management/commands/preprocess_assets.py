"""
Preprocess templatized asset files, enabling asset authors to use
Python/Django inside of Sass and CoffeeScript. This preprocessing
will happen before the invocation of the asset compiler (currently
handled by the assets paver file).

For this to work, assets need to be named with the appropriate
template extension (e.g., .mako for Mako templates). Currently Mako
is the only template engine supported.
"""

import glob
import os
import textwrap

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """
    Basic management command to preprocess asset template files.
    """

    help = "Preprocess asset template files to ready them for compilation."

    def handle(self, *args, **options):
        theme_name = getattr(settings, "THEME_NAME", None)
        use_custom_theme = settings.FEATURES.get("USE_CUSTOM_THEME", False)
        if not use_custom_theme or not theme_name:
            # No custom theme, nothing to do!
            return

        dest_dir = args[-1]
        for source_file in args[:-1]:
            self.process_one_file(source_file, dest_dir, theme_name)

    def process_one_file(self, source_file, dest_dir, theme_name):
        with open(source_file) as fsource:
            original_content = content = fsource.read()

        content = content.replace(
            "//<THEME-OVERRIDE>",
            "@import '{}';".format(theme_name),
            )

        if content != original_content:
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            dest_file = os.path.join(dest_dir, os.path.basename(source_file))
            with open(dest_file, "w") as fout:
                fout.write(textwrap.dedent("""\
                /*
                 * This file is dynamically generated and ignored by Git.
                 * DO NOT MAKE CHANGES HERE. Instead, go edit its source:
                 * {}
                 */
                \n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n
                """.format(source_file)))
                fout.write(content)


    def xxxx___handle_noargs(self, **options):
        """
        Walk over all of the static files directories specified in the
        settings file, looking for asset template files (indicated by
        a file extension like .mako).
        """
        for staticfiles_dir in getattr(settings, "STATICFILES_DIRS", []):
            # Cribbed from the django-staticfiles app at:
            # https://github.com/jezdez/django-staticfiles/blob/develop/staticfiles/finders.py#L52
            if isinstance(staticfiles_dir, (list, tuple)):
                prefix, staticfiles_dir = staticfiles_dir

            # Walk over the current static files directory tree,
            # preprocessing files that have a template extension.
            for root, dirs, files in os.walk(staticfiles_dir):
                for filename in files:
                    outfile, extension = os.path.splitext(filename)
                    # We currently only handle Mako templates
                    if extension == ".scss":
                        print("* {}/{}".format(root, filename))
                    if extension == ".mako":
                        self.__preprocess(os.path.join(root, filename),
                                          os.path.join(root, outfile))
