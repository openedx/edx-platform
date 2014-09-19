from rest_framework.reverse import reverse

from courseware.access import has_access

from edxval.api import (
    get_video_info_for_course_and_profile, ValInternalError
)


class BlockOutline(object):

    def __init__(self, course_id, start_block, categories_to_outliner, request, local_cache):
        """Create a BlockOutline using `start_block` as a starting point.

        `local_cache`
        """
        self.start_block = start_block
        self.categories_to_outliner = categories_to_outliner
        self.course_id = course_id
        self.request = request # needed for making full URLS
        self.local_cache = local_cache
        try:
            self.local_cache['course_videos'] = get_video_info_for_course_and_profile(
                unicode(course_id), "mobile_low"
            )
        except ValInternalError:
            self.local_cache['course_videos'] = {}


    def __iter__(self):
        child_to_parent = {}
        stack = [self.start_block]

        # path should be optional
        def path(block):
            block_path = []
            while block in child_to_parent:
                block = child_to_parent[block]
                if block is not self.start_block:
                    block_path.append({
                        'name': block.display_name,
                        'category': block.category,
                    })
            return reversed(block_path)

        def find_urls(block):
            block_path = []
            while block in child_to_parent:
                block = child_to_parent[block]
                block_path.append(block)

            course, chapter, section, unit = list(reversed(block_path))[:4]
            position = 1
            unit_name = unit.url_name
            for block in section.children:
                if block.name == unit_name:
                    break
                position += 1

            kwargs = dict(
                course_id=course.id.to_deprecated_string(),
                chapter=chapter.url_name,
                section=section.url_name
            )
            section_url = reverse(
                "courseware_section",
                kwargs=kwargs,
                request=self.request,
            )
            kwargs['position'] = position
            unit_url = reverse(
                "courseware_position",
                kwargs=kwargs,
                request=self.request,
            )
            return unit_url, section_url

        user = self.request.user

        while stack:
            curr_block = stack.pop()

            if curr_block.category in self.categories_to_outliner:
                if not has_access(user, 'load', curr_block, course_key=self.course_id):
                    continue

                summary_fn = self.categories_to_outliner[curr_block.category]
                block_path = list(path(block))
                unit_url, section_url = find_urls(block)
                yield {
                    "path": block_path,
                    "named_path": [b["name"] for b in block_path[:-1]],
                    "unit_url": unit_url,
                    "section_url": section_url,
                    "summary": summary_fn(self.course_id, curr_block, self.request, self.local_cache)
                }

            if curr_block.has_children:
                for block in reversed(curr_block.get_children()):
                    stack.append(block)
                    child_to_parent[block] = curr_block


def video_summary(course, course_id, video_descriptor, request, local_cache):
    # First try to check VAL for the URLs we want...
    val_video_info = local_cache['course_videos'].get(video_descriptor.edx_video_id)
    if val_video_info:
        video_url = val_video_info['url']
    # Then fall back to VideoDescriptor fields for video URLs
    elif video_descriptor.html5_sources:
        video_url = video_descriptor.html5_sources[0]
    else:
        video_url = video_descriptor.source

    # If we have the video information from VAL, we also have duration and size.
    if val_video_info:
        duration = val_video_info['duration']
        size = val_video_info['file_size']
    else:
        duration = None
        size = 0

    # Transcripts...
    usage_id_str = video_descriptor.scope_ids.usage_id._to_string()
    transcripts_langs_cache = local_cache['transcripts_langs']

    if usage_id_str in transcripts_langs_cache:
        transcript_langs = transcripts_langs_cache[usage_id_str]
    else:
        transcript_langs = video_descriptor.available_translations()
        transcripts_langs_cache[usage_id_str] = transcript_langs

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
        "language": video_descriptor.transcript_language,
        "category": video_descriptor.category,
        "id": usage_id_str
    }