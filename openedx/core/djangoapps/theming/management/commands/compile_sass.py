"""
Management command for compiling sass.

DEPRECATED in favor of `npm run compile-sass`.
"""
import shlex

from django.core.management import BaseCommand
from django.conf import settings

from pavelib.assets import run_deprecated_command_wrapper


class Command(BaseCommand):
    """
    Compile theme sass and collect theme assets.
    """

    help = "DEPRECATED. Use 'npm run compile-sass' instead."

    # NOTE (CCB): This allows us to compile static assets in Docker containers without database access.
    requires_system_checks = []

    def add_arguments(self, parser):
        """
            Add arguments for compile_sass command.

            Args:
                parser (django.core.management.base.CommandParser): parsed for parsing command line arguments.
        """
        parser.add_argument(
            'system', type=str, nargs='*', default=["lms", "cms"],
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
            help="DEPRECATED. Full recompilation is now always forced.",
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            default=False,
            help="Disable Sass compression",
        )

    def handle(self, *args, **options):
        """
        Handle compile_sass command.
        """
        systems = set(
            {"lms": "lms", "cms": "cms", "studio": "cms"}[sys]
            for sys in options.get("system", ["lms", "cms"])
        )
        theme_dirs = options.get("theme_dirs") or settings.COMPREHENSIVE_THEME_DIRS or []
        themes_option = options.get("themes") or []  # '[]' means 'all'
        if not settings.ENABLE_COMPREHENSIVE_THEMING:
            compile_themes = False
            themes = []
        elif "no" in themes_option:
            compile_themes = False
            themes = []
        elif "all" in themes_option:
            compile_themes = True
            themes = []
        else:
            compile_themes = True
            themes = themes_option
        run_deprecated_command_wrapper(
            old_command="./manage.py [lms|cms] compile_sass",
            ignored_old_flags=list(set(["force"]) & set(options)),
            new_command=shlex.join([
                "npm",
                "run",
                ("compile-sass-dev" if options.get("debug") else "compile-sass"),
                "--",
                *(["--skip-lms"] if "lms" not in systems else []),
                *(["--skip-cms"] if "cms" not in systems else []),
                *(["--skip-themes"] if not compile_themes else []),
                *(
                    arg
                    for theme_dir in theme_dirs
                    for arg in ["--theme-dir", str(theme_dir)]
                ),
                *(
                    arg
                    for theme in themes
                    for arg in ["--theme", theme]
                ),
            ]),
        )
