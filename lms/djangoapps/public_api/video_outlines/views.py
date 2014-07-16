"""
Video Outlines

We only provide the listing view for a video outline, and video outlines are
only displayed at the course level. This is because it makes it a lot easier to
optimize and reason about, and it avoids having to tackle the bigger problem of
general XBlock representation in this rather specialized formatting.
"""
from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.reverse import reverse
from rest_framework.response import Response
from rest_framework.views import APIView

from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from student.models import CourseEnrollment, User


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

            if curr_block.category in self.categories_to_outliner:
                summary_fn = self.categories_to_outliner[curr_block.category]
                block_path = list(path(block))
                yield {
                    "path": block_path,
                    "named_path": [b["name"] for b in block_path[:-1]],
                    "section_url": section_url(block),
                    "summary": summary_fn(curr_block)
                }

            if curr_block.has_children:
                for block in reversed(curr_block.get_children()):
                    stack.append(block)
                    child_to_parent[block] = curr_block


def video_summary(video_module):
    video_url = video_module.html5_sources[0] if video_module.html5_sources else video_module.source
    return {
        "video_url": video_url,
        "video_thumbnail_url": None,
        "duration": None,
        "size": 200000000,
        "name": video_module.display_name,
        "category": video_module.category,
        "id": video_module.scope_ids.usage_id._to_string()
    }


class VideoSummaryList(generics.ListAPIView):
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        course_id = SlashSeparatedCourseKey.from_deprecated_string(kwargs['course_id'])
        course = modulestore().get_course(course_id)
        video_outline = BlockOutline(course, {"video": video_summary}, request)

        return Response(video_outline)

