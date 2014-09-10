"""
Video Outlines

We only provide the listing view for a video outline, and video outlines are
only displayed at the course level. This is because it makes it a lot easier to
optimize and reason about, and it avoids having to tackle the bigger problem of
general XBlock representation in this rather specialized formatting.
"""
from functools import partial

from django.http import HttpResponse

from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.views import APIView
from public_api import get_mobile_course

from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.video_module.video_module import get_transcripts
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator

from student.models import CourseEnrollment, User
from courseware.model_data import FieldDataCache


class BlockOutline(object):

    def __init__(self, start_block, categories_to_outliner, request):
        """How to specify the kind of outline that'll be generated? Method?"""
        self.start_block = start_block
        self.categories_to_outliner = categories_to_outliner
        self.request = request # needed for making full URLS

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

        while stack:
            curr_block = stack.pop()

            if curr_block.category in self.categories_to_outliner:
                summary_fn = self.categories_to_outliner[curr_block.category]
                block_path = list(path(block))
                unit_url, section_url = find_urls(block)
                yield {
                    "path": block_path,
                    "named_path": [b["name"] for b in block_path[:-1]],
                    "unit_url": unit_url,
                    "section_url": section_url,
                    "summary": summary_fn(curr_block, self.request)
                }

            if curr_block.has_children:

                for block in reversed(curr_block.get_children()):
                    stack.append(block)
                    child_to_parent[block] = curr_block


def video_summary(course, video_descriptor, request):
    video_url = video_descriptor.html5_sources[0] if video_descriptor.html5_sources else video_descriptor.source
    #track_url, transcript_language, sorted_languages = get_transcripts(video_descriptor)
    #trans_url = video_descriptor.runtime.handler_url(video_descriptor, 'transcript', 'translation').rstrip('/?')
    #transcripts = {
    #    lang: request.build_absolute_uri(trans_url + '/' + lang)
    #    for lang in sorted_languages
    #}
    transcripts = {
        video_descriptor.transcript_language: video_descriptor
    }

    # this will be in a different format, so should it be included?
    # if track_url:
    #     transcripts["download"] = request.build_absolute_uri(track_url)
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
                    # This is horrible, terrible, no-good, very bad code, but it's
                    # 12:15AM and I need to push something to the sandbox tonight.
                    # Seriously, am I hashed or did key serialization behavior change
                    # again?
                    'course_id': course.id.to_deprecated_string().replace("/", "+"),
                    'block_id': video_descriptor.scope_ids.usage_id.block_id,
                    'lang': lang
                },
                request=request,
            )
            for lang in video_descriptor.available_translations()
        },
        "language": video_descriptor.transcript_language,
        "category": video_descriptor.category,
        "id": video_descriptor.scope_ids.usage_id._to_string()
    }


class VideoSummaryList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = CourseKey.from_string("course-v1:" + kwargs['course_id'])

        course = get_mobile_course(course_id)
        # this will cache all course assets so that subsequent calls (loading transcripts)
        # will hit the cache instead of mongo.
        contentstore().get_all_content_for_course(course.id)

        video_outline = BlockOutline(
            course, {"video": partial(video_summary, course)}, request
        )

        return Response(video_outline)


class VideoTranscripts(generics.RetrieveAPIView):
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        course_key = CourseKey.from_string("course-v1:" + kwargs['course_id'])
        block_id = kwargs['block_id']
        lang = kwargs['lang']

        usage_key = BlockUsageLocator(
            course_key, block_type="video", block_id=block_id
        )
        video_descriptor = modulestore().get_item(usage_key)
        content, filename, mimetype = video_descriptor.get_transcript(lang=lang)

        return HttpResponse(content, content_type=mimetype)


