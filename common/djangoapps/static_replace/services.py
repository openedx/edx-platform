"""
Supports replacement of static/course/jump-to-id URLs to absolute URLs in XBlocks.
"""

from xblock.reference.plugins import Service

from common.djangoapps.static_replace import (
    replace_course_urls,
    replace_jump_to_id_urls,
    replace_static_urls
)


class ReplaceURLService(Service):
    """
    A service for replacing static/course/jump-to-id URLs with absolute URLs in XBlocks.

    Args:
        course_id: Course identifier to be used in the absolute URL
        data_directory: (optional) Directory in which course data is stored
        static_asset_path: (optional) Path for static assets, which overrides data_directory and course_id, if nonempty
        static_paths_out: (optional) Array to collect tuples for each static URI found:
            * the original unmodified static URI
            * the updated static URI (will match the original if unchanged)
        jump_to_id_base_url: (optional) Absolute path to the base of the handler that will perform the redirect
        lookup_url_func: Lookup function which returns the correct path of the asset
    """
    def __init__(
        self,
        data_directory=None,
        course_id=None,
        static_asset_path='',
        static_paths_out=None,
        jump_to_id_base_url=None,
        lookup_asset_url=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.data_directory = data_directory
        self.course_id = course_id
        self.static_asset_path = static_asset_path
        self.static_paths_out = static_paths_out
        self.jump_to_id_base_url = jump_to_id_base_url
        self.lookup_asset_url = lookup_asset_url

    def replace_urls(self, text, static_replace_only=False):
        """
        Replaces all static/course/jump-to-id URLs in provided text/html.

        Args:
            text: String containing the URL to be replaced
            static_replace_only: If True, only static urls will be replaced
        """
        if self.lookup_asset_url:
            text = replace_static_urls(text, xblock=self.xblock(), lookup_asset_url=self.lookup_asset_url)
        else:
            text = replace_static_urls(
                text,
                data_directory=self.data_directory,
                course_id=self.course_id,
                static_asset_path=self.static_asset_path,
                static_paths_out=self.static_paths_out
            )
            if not static_replace_only:
                text = replace_course_urls(text, self.course_id)
                if self.jump_to_id_base_url:
                    text = replace_jump_to_id_urls(text, self.course_id, self.jump_to_id_base_url)

        return text
