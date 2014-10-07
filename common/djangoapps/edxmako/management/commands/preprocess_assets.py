"""
Preprocess templatized asset files, enabling asset authors to use
Python/Django inside of Sass and CoffeeScript. This preprocessing
will happen before the invocation of the asset compiler (currently
handled by the assets paver file).

For this to work, assets need to be named with the appropriate
template extension (e.g., .mako for Mako templates). Currently Mako
is the only template engine supported.
"""
import os

from django.core.management.base import NoArgsCommand
from django.conf import settings

from mako.template import Template
import textwrap

from shutil import rmtree, copytree

class Command(NoArgsCommand):
    """
    Basic management command to preprocess asset template files.
    """

    help = "Preprocess asset template files to ready them for compilation."

    def handle_noargs(self, **options):
        self.__rtl_sass()
        self.__preprocess_mako()

    def __rtl_sass(self):
        for staticfiles_dir in getattr(settings, "STATICFILES_DIRS", []):
            # Cribbed from the django-staticfiles app at:
            # https://github.com/jezdez/django-staticfiles/blob/develop/staticfiles/finders.py#L52
            if isinstance(staticfiles_dir, (list, tuple)):
                prefix, staticfiles_dir = staticfiles_dir

            ltr_sass = os.path.join(staticfiles_dir, 'sass')
            rtl_sass = os.path.join(staticfiles_dir, 'sass-rtl')

            if settings.FEATURES.get('ENABLE_RTL', False):
                if os.path.exists(ltr_sass):
                    if os.path.exists(rtl_sass):
                        rmtree(rtl_sass)

                    copytree(ltr_sass, rtl_sass)

            elif os.path.exists(rtl_sass):
                # Removes the RTL files after switching off ENABLE_RTL feature
                # To avoid compilation
                rmtree(rtl_sass)


    def __preprocess_mako(self):
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
                    if extension == ".mako":
                        is_rtl = 'sass-rtl' in root
                        self.__preprocess(os.path.join(root, filename),
                                          os.path.join(root, outfile),
                                          is_rtl)


    def __context(self, is_rtl=False):
        """
        Return a dict that contains all of the available context
        variables to the asset template.
        """
        # TODO: do we need to include anything else?
        # TODO: do this with the django-settings-context-processor
        return {
            "FEATURES": settings.FEATURES,
            "RTL": is_rtl,
            "THEME_NAME": getattr(settings, "THEME_NAME", None),
        }


    def __preprocess(self, infile, outfile, is_rtl=False):
        """
        Run `infile` through the Mako template engine, storing the
        result in `outfile`.
        """
        with open(outfile, "w") as _outfile:
            _outfile.write(textwrap.dedent("""\
            /*
             * This file is dynamically generated and ignored by Git.
             * DO NOT MAKE CHANGES HERE. Instead, go edit its template:
             * %s
             */
            """ % infile))
            _outfile.write(Template(filename=str(infile)).render(env=self.__context(is_rtl)))

