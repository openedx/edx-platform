"""
Download the translations via atlas for the XBlocks.
"""

from openedx.core.djangoapps.plugins.i18n_api import BaseAtlasPullCommand
from xmodule.modulestore import api as xmodule_api

from ...translation import xblocks_atlas_pull


class Command(BaseAtlasPullCommand):
    """
    Pull the XBlock translations via atlas for the XBlocks.

    For detailed information about atlas pull options check the atlas documentation:

     - https://github.com/openedx/openedx-atlas
    """

    def handle(self, *args, **options):
        xblock_translations_root = xmodule_api.get_python_locale_root()
        self.ensure_empty_directory(xblock_translations_root)

        atlas_pull_options = self.get_atlas_pull_options(**options)
        xblocks_atlas_pull(pull_options=atlas_pull_options)
