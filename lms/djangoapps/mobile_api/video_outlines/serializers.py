"""
Serializer for video outline
"""
from rest_framework.reverse import reverse

from courseware.access import has_access

from edxval.api import (
    get_video_info_for_course_and_profile, ValInternalError
)


class BlockOutline(object):
    """
    Serializes course videos, pulling data from VAL and the video modules.
    """
    def __init__(self, course_id, start_block, categories_to_outliner, request):
        """Create a BlockOutline using `start_block` as a starting point."""
        self.start_block = start_block
        self.categories_to_outliner = categories_to_outliner
        self.course_id = course_id
        self.request = request  # needed for making full URLS
        self.local_cache = {}
        try:
            self.local_cache['course_videos'] = get_video_info_for_course_and_profile(
                unicode(course_id), "mobile_low"
            )
        except ValInternalError:  # pragma: nocover
            self.local_cache['course_videos'] = {}

    def __iter__(self):
        child_to_parent = {}
        stack = [self.start_block]

        # path should be optional
        def path(block):
            """path for block"""
            block_path = []
            while block in child_to_parent:
                block = child_to_parent[block]
                if block is not self.start_block:
                    block_path.append({
                        # to be consistent with other edx-platform clients, return the defaulted display name
                        'name': block.display_name_with_default,
                        'category': block.category,
                        'id': unicode(block.location)
                    })
            return reversed(block_path)

        def find_urls(block):
            """
            Find the section and unit urls for a block.

            Returns:
                unit_url, section_url:
                    unit_url (str): The url of a unit
                    section_url (str): The url of a section

            """
            block_path = []
            while block in child_to_parent:
                block = child_to_parent[block]
                block_path.append(block)

            block_list = list(reversed(block_path))
            block_count = len(block_list)

            chapter_id = block_list[1].location.block_id if block_count > 1 else None
            section = block_list[2] if block_count > 2 else None
            position = None

            #position is found traversing the section block
            if block_count > 3:
                position = 1
                for block in section.children:
                    if block.name == block_list[3].url_name:
                        break
                    position += 1

            if chapter_id is None:
                no_chapter_url = reverse(
                    "courseware",
                    kwargs=dict(
                        course_id=unicode(self.course_id),
                    ),
                    request=self.request
                )
                return no_chapter_url, no_chapter_url
            elif section is None:
                no_section_url = reverse(
                    "courseware_chapter",
                    kwargs=dict(
                        course_id=unicode(self.course_id),
                        chapter=chapter_id
                    ),
                    request=self.request
                )
                return no_section_url, no_section_url
            elif position is None:
                no_position_url = reverse(
                    "courseware_section",
                    kwargs=dict(
                        course_id=unicode(self.course_id),
                        chapter=chapter_id,
                        section=section.url_name
                    ),
                    request=self.request
                )
                return no_position_url, no_position_url
            else:
                section_url = reverse(
                    "courseware_section",
                    kwargs=dict(
                        course_id=unicode(self.course_id),
                        chapter=chapter_id,
                        section=section.url_name
                    ),
                    request=self.request
                )
                unit_url = reverse(
                    "courseware_position",
                    kwargs=dict(
                        course_id=unicode(self.course_id),
                        chapter=chapter_id,
                        section=section.url_name,
                        position=position
                    ),
                    request=self.request
                )
                return unit_url, section_url

        user = self.request.user

        while stack:
            curr_block = stack.pop()

            if curr_block.hide_from_toc:
                # For now, if the 'hide_from_toc' setting is set on the block, do not traverse down
                # the hierarchy.  The reason being is that these blocks may not have human-readable names
                # to display on the mobile clients.
                # Eventually, we'll need to figure out how we want these blocks to be displayed on the
                # mobile clients.  As, they are still accessible in the browser, just not navigatable
                # from the table-of-contents.
                continue

            if curr_block.category in self.categories_to_outliner:
                if not has_access(user, 'load', curr_block, course_key=self.course_id):
                    continue

                summary_fn = self.categories_to_outliner[curr_block.category]
                block_path = list(path(curr_block))
                unit_url, section_url = find_urls(curr_block)

                yield {
                    "path": block_path,
                    "named_path": [b["name"] for b in block_path],
                    "unit_url": unit_url,
                    "section_url": section_url,
                    "summary": summary_fn(self.course_id, curr_block, self.request, self.local_cache)
                }

            if curr_block.has_children:
                for block in reversed(curr_block.get_children()):
                    stack.append(block)
                    child_to_parent[block] = curr_block


def video_summary(course, course_id, video_descriptor, request, local_cache):
    """
    returns summary dict for the given video module
    """
    # First try to check VAL for the URLs we want.
    val_video_info = local_cache['course_videos'].get(video_descriptor.edx_video_id, {})
    if val_video_info:
        video_url = val_video_info['url']
    # Then fall back to VideoDescriptor fields for video URLs
    elif video_descriptor.html5_sources:
        video_url = video_descriptor.html5_sources[0]
    else:
        video_url = video_descriptor.source

    # If we have the video information from VAL, we also have duration and size.
    duration = val_video_info.get('duration', None)
    size = val_video_info.get('file_size', 0)

    # Transcripts...
    transcript_langs = video_descriptor.available_translations(verify_assets=False)

    transcripts = {
        lang: reverse(
            'video-transcripts-detail',
            kwargs={
                'course_id': unicode(course_id),
                'block_id': video_descriptor.scope_ids.usage_id.block_id,
                'lang': lang
            },
            request=request,
        )
        for lang in transcript_langs
    }

    return {
        "video_url": video_url,
        "video_thumbnail_url": None,
        "duration": duration,
        "size": size,
        "name": video_descriptor.display_name,
        "transcripts": transcripts,
        "language": video_descriptor.get_default_transcript_language(),
        "category": video_descriptor.category,
        "id": unicode(video_descriptor.scope_ids.usage_id),
    }
