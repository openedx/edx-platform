"""
Management command for compiling sass.
"""

from __future__ import unicode_literals

from django.core.management import BaseCommand, CommandError

from paver.easy import call_task

from pavelib.assets import ALL_SYSTEMS
from openedx.core.djangoapps.theming.helpers import get_themes, get_theme_base_dirs, is_comprehensive_theming_enabled


class Command(BaseCommand):
    """
    Compile theme sass and collect theme assets.
    """

    help = 'Compile and collect themed assets...'

    def add_arguments(self, parser):
        """
            Add arguments for compile_sass command.

            Args:
                parser (django.core.management.base.CommandParser): parsed for parsing command line arguments.
        """
        parser.add_argument(
            'system', type=str, nargs='*', default=ALL_SYSTEMS,
            help="lms or studio",
        )

        # Named (optional) arguments
        parser.add_argument(
            '--theme-dirs',
            dest='theme_dirs',
            type=str,
            nargs='+',
            default=None,
            help="List of dirs where given themes would be looked.",
        )

        parser.add_argument(
            '--themes',
            type=str,
            nargs='+',
            default=["all"],
            help="List of themes whose sass need to compiled. Or 'no'/'all' to compile for no/all themes.",
        )

        # Named (optional) arguments
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help="Force full compilation",
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            default=False,
            help="Disable Sass compression",
        )

    @staticmethod
    def parse_arguments(*args, **options):  # pylint: disable=unused-argument
        """
        Parse and validate arguments for compile_sass command.

        Args:
            *args: Positional arguments passed to the update_assets command
            **options: optional arguments passed to the update_assets command
        Returns:
            A tuple containing parsed values for themes, system, source comments and output style.
            1. system (list): list of system names for whom to compile theme sass e.g. 'lms', 'cms'
            2. theme_dirs (list): list of Theme objects
            3. themes (list): list of Theme objects
            4. force (bool): Force full compilation
            5. debug (bool): Disable Sass compression
        """
        system = options.get("system", ALL_SYSTEMS)
        given_themes = options.get("themes", ["all"])
        theme_dirs = options.get("theme_dirs", None)

        force = options.get("force", True)
        debug = options.get("debug", True)

        if theme_dirs:
            available_themes = {}
            for theme_dir in theme_dirs:
                available_themes.update({t.theme_dir_name: t for t in get_themes(theme_dir)})
        else:
            theme_dirs = get_theme_base_dirs()
            available_themes = {t.theme_dir_name: t for t in get_themes()}

        if 'no' in given_themes or 'all' in given_themes:
            # Raise error if 'all' or 'no' is present and theme names are also given.
            if len(given_themes) > 1:
                raise CommandError("Invalid themes value, It must either be 'all' or 'no' or list of themes.")
        # Raise error if any of the given theme name is invalid
        # (theme name would be invalid if it does not exist in themes directory)
        elif (not set(given_themes).issubset(available_themes.keys())) and is_comprehensive_theming_enabled():
            raise CommandError(
                "Given themes '{themes}' do not exist inside any of the theme directories '{theme_dirs}'".format(
                    themes=", ".join(set(given_themes) - set(available_themes.keys())),
                    theme_dirs=theme_dirs,
                ),
            )

        if "all" in given_themes:
            themes = list(available_themes.itervalues())
        elif "no" in given_themes:
            themes = []
        else:
            # convert theme names to Theme objects, this will remove all themes if theming is disabled
            themes = [available_themes.get(theme) for theme in given_themes if theme in available_themes]

        return system, theme_dirs, themes, force, debug

    def handle(self, *args, **options):
        """
        Handle compile_sass command.
        """
        system, theme_dirs, themes, force, debug = self.parse_arguments(*args, **options)
        themes = [theme.theme_dir_name for theme in themes]

        if options.get("themes", None) and not is_comprehensive_theming_enabled():
            # log a warning message to let the user know that asset compilation for themes is skipped
            self.stdout.write(
                self.style.WARNING(  # pylint: disable=no-member
                    "Skipping theme asset compilation: enable theming to process themed assets"
                ),
            )

        call_task(
            'pavelib.assets.compile_sass',
            options={'system': system, 'theme_dirs': theme_dirs, 'themes': themes, 'force': force, 'debug': debug},
        )
