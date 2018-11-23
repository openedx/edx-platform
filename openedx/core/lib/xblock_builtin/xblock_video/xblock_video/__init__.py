"""
Container for video module and its utils.
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from web_fragments.fragment import Fragment
from xblock.core import XBlock

from openedx.core.lib.xblock_builtin import get_css_dependencies, get_js_dependencies
from .video_handlers import VideoStudentViewHandlers, VideoStudioViewHandlers
from .video_xfields import VideoFields

# pylint: disable=wildcard-import

from .transcripts_utils import *
from .video_utils import *
from .video_module import *
from .bumper_utils import *


@XBlock.wants("request", "request_cache", "settings", "completion")
class VideoXBlock(
        VideoFields,
        VideoMixin,
        VideoDescriptor,
        VideoTranscriptsMixin,
        VideoStudentViewHandlers,
        VideoStudioViewHandlers,
        LicenseMixin,
        XBlock):
    """
    Video XBlock

    XML source example:
        <video show_captions="true"
            youtube="0.75:jNCf2gIqpeE,1.0:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg"
            url_name="lecture_21_3" display_name="S19V3: Vacancies"
        >
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.mp4"/>
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.webm"/>
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.ogv"/>
        </video>
    """
    has_custom_completion = True
    completion_mode = XBlockCompletionMode.COMPLETABLE

    video_time = 0
    icon_class = 'video'

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        Return a fragment with the html from this XBlock
        Makes no use of the context parameter
        """
        fragment = Fragment()
        self.add_resource_urls(fragment)
        fragment.add_content(self.get_html())
        fragment.initialize_js('VideoXBlock')
        return fragment

    @staticmethod
    def css_dependencies():
        """
        Returns list of CSS files that this XBlock depends on.
        """
        return get_css_dependencies('style-video')

    @staticmethod
    def js_dependencies():
        """
        Returns list of JS files that this XBlock depends on.
        """
        return get_js_dependencies('video')

    def add_resource_urls(self, fragment):
        """
        Adds URLs for static resources that this XBlock depends on to `fragment`.
        """
        for css_file in self.css_dependencies():
            fragment.add_css_url(staticfiles_storage.url(css_file))

        # Body dependencies
        for js_file in self.js_dependencies():
            fragment.add_javascript_url(staticfiles_storage.url(js_file))
