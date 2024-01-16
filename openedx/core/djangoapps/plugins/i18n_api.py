"""
edx-platform specific i18n helpers for edx-django-utils plugins.
"""

from dataclasses import dataclass, asdict
import os
from pathlib import Path
import subprocess


@dataclass
class ArgparseArgument:
    """
    Argument specs to be used with argparse add_argument method.
    """

    flag: str = None  # This is passed as a positional argument
    dest: str = None
    help: str = None

    def get_kwargs(self):
        """
        Return keyword arguments for the `add_argument` method .
        """
        argument_dict = asdict(self)
        argument_dict.pop('flag')
        return argument_dict

    def get_args(self):
        """
        Return positional arguments for the `add_argument` method .
        """
        return [self.flag]


# `atlas pull` arguments defintions.
#
#  - https://github.com/openedx/openedx-atlas
#
ATLAS_ARGUMENTS = [
    ArgparseArgument(
        flag='--filter',
        dest='filter',
        help='Filter option for `atlas pull` e.g. --filter=ar,fr_CA,de_DE.'
    ),
    ArgparseArgument(
        flag='--repository',
        dest='repository',
        help='Custom repository slug for `atlas pull` e.g. '
             '--repository=friendsofopenedx/openedx-translations . '
             'Default is "openedx/openedx-translations".'
    ),
    ArgparseArgument(
        flag='--branch',
        dest='branch',
        help='Custom branch for "atlas pull" e.g. --branch=release/redwood . Default is "main".',
    ),
]


def atlas_pull_by_modules(module_names, locale_root, pull_options):
    """
    Atlas pull translations by module name instead of repository name.
    """
    atlas_pull_args = [
        # Asterisk (*) is used instead of the repository name because it's not known at runtime.
        # The `--expand-glob` option is used to expand match any repository name that has the right module name.
        f'translations/*/{module_name}/conf/locale:{module_name}'
        for module_name in module_names
    ]

    subprocess.run(
        args=['atlas', 'pull', '--expand-glob', *pull_options, *atlas_pull_args],
        check=True,
        cwd=locale_root,
    )


def compile_po_files(root_dir):
    """
    Compile the .po files into .mo files recursively in the given directory.

    Mimics the behavior of `django-admin compilemessages` for the po files but for any directory.
    """
    for root, _dirs, files in os.walk(root_dir):
        root = Path(root)
        for po_file in files:
            if po_file.endswith('.po'):
                po_file_path = root / po_file
                subprocess.run(
                    args=['msgfmt', '--check-format', '-o', str(po_file_path.with_suffix('.mo')), str(po_file_path)],
                    check=True,
                )
