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

from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.video_module.video_module import get_transcripts
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator

# from xmodule.xmodule.video_module.transcripts_utils import Transcript

from student.models import CourseEnrollment, User
from courseware.module_render import get_module_system_for_user
from courseware.model_data import FieldDataCache


class BlockOutline(object):

    def __init__(self, start_block, categories_to_outliner, request, system):
        """How to specify the kind of outline that'll be generated? Method?"""
        self.start_block = start_block
        self.categories_to_outliner = categories_to_outliner
        self.request = request # needed for making full URLS
        self.system = system

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

        def section_url(block):
            block_path = []
            while block in child_to_parent:
                block = child_to_parent[block]
                block_path.append(block)
            course, chapter, section = list(reversed(block_path))[:3]
            return reverse(
                "courseware_section",
                kwargs=dict(
                    course_id=course.id.to_deprecated_string(),
                    chapter=chapter.url_name,
                    section=section.url_name,
                ),
                request=self.request,
            )

        while stack:
            curr_block = stack.pop()
            curr_block.runtime = self.system

            if curr_block.category in self.categories_to_outliner:
                summary_fn = self.categories_to_outliner[curr_block.category]
                block_path = list(path(block))
                yield {
                    "path": block_path,
                    "named_path": [b["name"] for b in block_path[:-1]],
                    "section_url": section_url(block),
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
        course = modulestore().get_course(course_id)
        system, _student_data = get_module_system_for_user(
            user=request.user,
            field_data_cache=FieldDataCache([course], course_id, request.user),
            descriptor=course,
            course_id=course_id,
            track_function=None,
            xqueue_callback_url_prefix=None,
            request_token='video_api',
        )
        system.export_fs = None
        video_outline = BlockOutline(
            course, {"video": partial(video_summary, course)}, request, system
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
            course_key,
            block_type="video",
            block_id=block_id
        )
        video_descriptor = modulestore().get_item(usage_key)
        content, filename, mimetype = video_descriptor.get_transcript(lang=lang)

        return HttpResponse(content, content_type=mimetype)


