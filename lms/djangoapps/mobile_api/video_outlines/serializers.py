from rest_framework.reverse import reverse

from courseware.access import has_access

from edxval.api import get_videos_for_course, get_video_info, ValInternalError, ValVideoNotFoundError


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


    def __iter__(self):
        child_to_parent = {}
        stack = [self.start_block]

        self.local_cache['course_videos'] = {v['edx_video_id']: v for v in get_videos_for_course(self.course_id)}

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
    duration = None
    size = 200000000
    video_url = ''

    if video_descriptor.edx_video_id:
        try:
            video_info = local_cache['course_videos'][video_descriptor.edx_video_id]
        except KeyError:
            print 'could not find', video_descriptor.edx_video_id
        else:
            for enc in video_info['encoded_videos']:
                video_url = enc['url']
                size = enc['file_size']
                if enc['profile'] == 'mobile':
                    break
            transcripts = {sub['lang']: sub['content_url'] for sub in video_info['subtitles']}
            duration = video_info['duration']

    if not video_url:
        if video_descriptor.html5_sources:
            video_url = video_descriptor.html5_sources[0]
        else:
            video_url = video_descriptor.source

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
    # import pdb; pdb.set_trace()

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