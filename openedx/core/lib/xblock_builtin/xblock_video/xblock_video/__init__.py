"""
Container for video module and its utils.
"""

from django.contrib.staticfiles.storage import staticfiles_storage
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.completable import XBlockCompletionMode

from openedx.core.lib.xblock_builtin import get_css_dependencies, get_js_dependencies
from xmodule.xml_module import XmlParserMixin
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
        VideoEditingMixins,
        VideoTranscriptsMixin,
        VideoStudentViewHandlers,
        VideoStudioViewHandlers,
        XBlock,
        XmlParserMixin):
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

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Parses OLX into XBlock.

        This method is overridden here to allow parsing legacy OLX, coming from video XModule.
        XBlock stores all the associated data, fields and children in a XML element inlined into vertical XML file
        XModule stored only minimal data on the element included into vertical XML and used a dedicated "video"
        folder in OLX to store fields and children.

        If no external data sources are found (file in "video" folder), it is exactly equivalent to base method
        XBlock.parse_xml. Otherwise this method parses file in "video" folder (known as definition_xml) and updates fields accordingly.
        """
        block = super(VideoXBlock, cls).parse_xml(node, runtime, keys, id_generator)

        cls._apply_translations_to_node_attributes(block, node)
        cls._apply_metadata_and_policy(block, node, runtime)

        # Update VAL with info extracted from `xml_object`
        block.edx_video_id = block.import_video_info_into_val(
            node,
            runtime.resources_fs,
            getattr(id_generator, 'target_course_id', None)
        )

        return block

    @classmethod
    def _apply_translations_to_node_attributes(cls, block, node):
        """
        Applies metadata translations for attributes stored on an inlined XML element.
        """
        for old_attr, target_attr in cls.metadata_translations.iteritems():
            if old_attr in node.attrib and hasattr(block, target_attr):
                setattr(block, target_attr, node.attrib[old_attr])

    @classmethod
    def _apply_metadata_and_policy(cls, block, node, runtime):
        """
        If this block is a pointer to a "video" folder in OLX, than parse it and update block fields
        Attempt to load definition XML from "video" folder in OLX.
        """
        try:
            definition_xml, _ = cls.load_definition_xml(node, runtime, block.scope_ids.def_id)
        except Exception as err:  # pylint: disable=broad-except
            log.info(
                "Exception %s when trying to load definition xml for block %s - assuming XBlock export format",
                err,
                block
            )
            return

        metadata = cls.load_metadata(definition_xml)
        # FIXME: are there any video data in the policy.json, like there were with Discussions?
        # If not, should we skip this step?
        cls.apply_policy(metadata, runtime.get_policy(block.block_id))

        for field_name, value in metadata.iteritems():
            if field_name in block.fields:
                setattr(block, field_name, value)
