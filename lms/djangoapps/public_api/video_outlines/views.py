"""
Video Outlines

We only provide the listing view for a video outline, and video outlines are
only displayed at the course level. This is because it makes it a lot easier to
optimize and reason about, and it avoids having to tackle the bigger problem of
general XBlock representation in this rather specialized formatting.
"""
from functools import partial

from django.core.cache import cache
from django.http import HttpResponse

from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.views import APIView
from public_api import get_mobile_course

from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.video_module.video_module import get_transcripts
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator

from student.models import CourseEnrollment, User
from courseware.model_data import FieldDataCache
from courseware.access import has_access


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

    # import pdb; pdb.set_trace()

    return {
        "video_url": video_url,
        "video_thumbnail_url": None,
        "duration": None,
        "size": 200000000,
        "name": video_descriptor.display_name,
        "transcripts": {
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
        },
        "language": video_descriptor.transcript_language,
        "category": video_descriptor.category,
        "id": usage_id_str
    }


class VideoSummaryList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = CourseKey.from_string(kwargs['course_id'])
        course = get_mobile_course(course_id)

        transcripts_cache_key = "VideoSummaryList.transcripts.langs.{}".format(course_id)
        original_transcripts_langs_cache = cache.get(transcripts_cache_key, {})
        local_cache = {'transcripts_langs': dict(original_transcripts_langs_cache)}

        video_outline = list(
            BlockOutline(
                course_id,
                course,
                {"video": partial(video_summary, course)},
                request,
                local_cache,
            )
        )
        # If we added any entries, renew the cache...
        if local_cache['transcripts_langs'] != original_transcripts_langs_cache:
            cache.set(transcripts_cache_key, local_cache['transcripts_langs'])

        return Response(video_outline)


class VideoTranscripts(generics.RetrieveAPIView):
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        course_key = CourseKey.from_string(kwargs['course_id'])
        block_id = kwargs['block_id']
        lang = kwargs['lang']

        usage_key = BlockUsageLocator(
            course_key, block_type="video", block_id=block_id
        )
        video_descriptor = modulestore().get_item(usage_key)
        content, filename, mimetype = video_descriptor.get_transcript(lang=lang)

        return HttpResponse(content, content_type=mimetype)


