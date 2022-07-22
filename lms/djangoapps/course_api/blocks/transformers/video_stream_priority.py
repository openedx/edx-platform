"""
Video block stream priority Transformer
"""

from openedx.core.djangoapps.content.block_structure.transformer import BlockStructureTransformer
from openedx.core.djangoapps.video_pipeline.config.waffle import DEPRECATE_YOUTUBE

from .student_view import StudentViewTransformer


class VideoBlockStreamPriorityTransformer(BlockStructureTransformer):
    """
    Transformer to add stream priority for encoded_videos.
    If DEPRECATE_YOUTUBE flag is on for a course, Youtube videos have
    highest priority i.e. 0. Else, the default priority for videos is
    as shown in DEFAULT_VIDEO_STREAM_PRIORITY below.
    """

    @classmethod
    def name(cls):
        return "video_stream_priority"

    WRITE_VERSION = 1
    READ_VERSION = 1
    DEFAULT_VIDEO_STREAM_PRIORITY = {
        'hls': 0,
        'mobile_low': 1,
        'mobile_high': 2,
        'desktop_mp4': 3,
        'fallback': 4,
        'youtube': 5,
    }
    DEPRECATE_YOUTUBE_VIDEO_STREAM_PRIORITY = {
        'youtube': 0,
        'hls': 1,
        'mobile_low': 2,
        'mobile_high': 3,
        'desktop_mp4': 4,
        'fallback': 5,
    }

    def transform(self, usage_info, block_structure):
        """
        Write all the video blocks' stream priority.

        For the encoded_videos dictionary, a field called stream_priority
        will be added to all the available video blocks. Client end can use this
        value to prioritise streaming for different video formats.
        """

        for block_key in block_structure.topological_traversal(
            filter_func=lambda block_key: block_key.block_type == 'video',
            yield_descendants_of_unyielded=True,
        ):
            student_view_data = block_structure.get_transformer_block_field(
                block_key, StudentViewTransformer, StudentViewTransformer.STUDENT_VIEW_DATA
            )
            if not student_view_data:
                return

            # web-only videos don't contain any video information for native clients
            only_on_web = student_view_data.get('only_on_web')
            if only_on_web:
                continue
            encoded_videos = student_view_data.get('encoded_videos')
            for video_format, video_data in encoded_videos.items():
                if DEPRECATE_YOUTUBE.is_enabled(usage_info.course_key):
                    video_data['stream_priority'] = self.DEPRECATE_YOUTUBE_VIDEO_STREAM_PRIORITY[video_format]
                else:
                    video_data['stream_priority'] = self.DEFAULT_VIDEO_STREAM_PRIORITY[video_format]
