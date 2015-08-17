"""
Serializer for video outline
"""
from rest_framework.reverse import reverse

from xmodule.modulestore.mongo.base import BLOCK_TYPES_WITH_CHILDREN
from xmodule.modulestore.django import modulestore
from courseware.access import has_access
from courseware.courses import get_course_by_id
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor
from util.module_utils import get_dynamic_descriptor_children

from edxval.api import (
    get_video_info_for_course_and_profiles, ValInternalError
)


class BlockOutline(object):
    """
    Serializes course videos, pulling data from VAL and the video modules.
    """
    def __init__(self, course_id, start_block, block_types, request, video_profiles):
        """Create a BlockOutline using `start_block` as a starting point."""
        self.start_block = start_block
        self.block_types = block_types
        self.course_id = course_id
        self.request = request  # needed for making full URLS
        self.local_cache = {}
        try:
            self.local_cache['course_videos'] = get_video_info_for_course_and_profiles(
                unicode(course_id), video_profiles
            )
        except ValInternalError:  # pragma: nocover
            self.local_cache['course_videos'] = {}

    def __iter__(self):
        def parent_or_requested_block_type(usage_key):
            """
            Returns whether the usage_key's block_type is one of self.block_types or a parent type.
            """
            return (
                usage_key.block_type in self.block_types or
                usage_key.block_type in BLOCK_TYPES_WITH_CHILDREN
            )

        def create_module(descriptor):
            """
            Factory method for creating and binding a module for the given descriptor.
            """
            field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
                self.course_id, self.request.user, descriptor, depth=0,
            )
            course = get_course_by_id(self.course_id)
            return get_module_for_descriptor(
                self.request.user, self.request, descriptor, field_data_cache, self.course_id, course=course
            )

        with modulestore().bulk_operations(self.course_id):
            child_to_parent = {}
            stack = [self.start_block]
            while stack:
                curr_block = stack.pop()

                if curr_block.hide_from_toc:
                    # For now, if the 'hide_from_toc' setting is set on the block, do not traverse down
                    # the hierarchy.  The reason being is that these blocks may not have human-readable names
                    # to display on the mobile clients.
                    # Eventually, we'll need to figure out how we want these blocks to be displayed on the
                    # mobile clients.  As they are still accessible in the browser, just not navigatable
                    # from the table-of-contents.
                    continue

                if curr_block.location.block_type in self.block_types:
                    if not has_access(self.request.user, 'load', curr_block, course_key=self.course_id):
                        continue

                    summary_fn = self.block_types[curr_block.category]
                    block_path = list(path(curr_block, child_to_parent, self.start_block))
                    unit_url, section_url = find_urls(self.course_id, curr_block, child_to_parent, self.request)

                    yield {
                        "path": block_path,
                        "named_path": [b["name"] for b in block_path],
                        "unit_url": unit_url,
                        "section_url": section_url,
                        "summary": summary_fn(self.course_id, curr_block, self.request, self.local_cache)
                    }

                if curr_block.has_children:
                    children = get_dynamic_descriptor_children(
                        curr_block,
                        self.request.user.id,
                        create_module,
                        usage_key_filter=parent_or_requested_block_type
                    )
                    for block in reversed(children):
                        stack.append(block)
                        child_to_parent[block] = curr_block


def path(block, child_to_parent, start_block):
    """path for block"""
    block_path = []
    while block in child_to_parent:
        block = child_to_parent[block]
        if block is not start_block:
            block_path.append({
                # to be consistent with other edx-platform clients, return the defaulted display name
                'name': block.display_name_with_default,
                'category': block.category,
                'id': unicode(block.location)
            })
    return reversed(block_path)


def find_urls(course_id, block, child_to_parent, request):
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

    if block_count > 3:
        position = 1
        for block in section.children:
            if block.name == block_list[3].url_name:
                break
            position += 1

    kwargs = {'course_id': unicode(course_id)}
    if chapter_id is None:
        course_url = reverse("courseware", kwargs=kwargs, request=request)
        return course_url, course_url

    kwargs['chapter'] = chapter_id
    if section is None:
        chapter_url = reverse("courseware_chapter", kwargs=kwargs, request=request)
        return chapter_url, chapter_url

    kwargs['section'] = section.url_name
    section_url = reverse("courseware_section", kwargs=kwargs, request=request)
    if position is None:
        return section_url, section_url

    kwargs['position'] = position
    unit_url = reverse("courseware_position", kwargs=kwargs, request=request)
    return unit_url, section_url


def video_summary(video_profiles, course_id, video_descriptor, request, local_cache):
    """
    returns summary dict for the given video module
    """
    always_available_data = {
        "name": video_descriptor.display_name,
        "category": video_descriptor.category,
        "id": unicode(video_descriptor.scope_ids.usage_id),
        "only_on_web": video_descriptor.only_on_web,
    }

    if video_descriptor.only_on_web:
        ret = {
            "video_url": None,
            "video_thumbnail_url": None,
            "duration": 0,
            "size": 0,
            "transcripts": {},
            "language": None,
        }
        ret.update(always_available_data)
        return ret

    # Get encoded videos
    video_data = local_cache['course_videos'].get(video_descriptor.edx_video_id, {})

    # Get highest priority video to populate backwards compatible field
    default_encoded_video = {}

    if video_data:
        for profile in video_profiles:
            default_encoded_video = video_data['profiles'].get(profile, {})
            if default_encoded_video:
                break

    if default_encoded_video:
        video_url = default_encoded_video['url']
    # Then fall back to VideoDescriptor fields for video URLs
    elif video_descriptor.html5_sources:
        video_url = video_descriptor.html5_sources[0]
    else:
        video_url = video_descriptor.source

    # Get duration/size, else default
    duration = video_data.get('duration', None)
    size = default_encoded_video.get('file_size', 0)

    # Transcripts...
    transcripts_info = video_descriptor.get_transcripts_info()
    transcript_langs = video_descriptor.available_translations(transcripts_info, verify_assets=False)

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

    ret = {
        "video_url": video_url,
        "video_thumbnail_url": None,
        "duration": duration,
        "size": size,
        "transcripts": transcripts,
        "language": video_descriptor.get_default_transcript_language(transcripts_info),
        "encoded_videos": video_data.get('profiles')
    }
    ret.update(always_available_data)
    return ret
