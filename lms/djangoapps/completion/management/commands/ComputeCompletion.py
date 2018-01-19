from collections import deque

from django.core.management.base import BaseCommand, CommandError

from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from lms.djangoapps.course_api.blocks.api import get_blocks
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from student.tests.factories import UserFactory

class Command(BaseCommand):

    def handle(self, *args, **options):
        course_name = 'course-v1:wert+qw4tqw4t+qertqert'
        course_usage_key = self._create_course_usage_key(course_name)

        user = UserFactory.create(
            username="staff",
            email="staff@example.com"
            )
        site = SiteFactory.create()

        with emulate_http_request(site, user) as request:
            import cProfile

            api_raw_course_data = get_blocks(
                request, 
                course_usage_key,
                user=user,
                requested_fields=['completion', 'children']
            )
            name_of_course_root = api_raw_course_data['root']
            course_blocks = api_raw_course_data['blocks']

            print "== get_blocks =="
            cProfile.runctx('get_blocks(request, course_usage_key, user=user, requested_fields=[\'completion\', \'children\'])', globals(), locals())

            print "== Calculate Completion DFS =="
            cProfile.runctx('self._compute_course_completion(name_of_course_root, course_blocks)', globals(), locals())


    def _create_course_usage_key(self, course_name):
        course_key = CourseKey.from_string(course_name)
        return modulestore().make_course_usage_key(course_key)


    def _compute_course_completion(self, name_of_root_block, course_blocks):
        # print "Number of course_blocks: %d" % (len(course_blocks)) 

        course_completion = self._tally_completion_depth_first(
            course_blocks[name_of_root_block],
            course_blocks 
        )

        # print "Number of completed blocks: %f" % (course_completion)


    def _tally_completion_depth_first(self, current_block, course_blocks):
        names_of_children = current_block.get('children', None)
        completion_at_current_block = 0.0

        if names_of_children:
            completion_at_current_block += self._compute_completion_of_children(
                names_of_children,
                course_blocks
            )
        else:
            completion_at_current_block = current_block.get('completion', 0.0)

        return completion_at_current_block


    def _compute_completion_of_children(self, names_of_children, course_blocks):
        completion_of_children = 0.0
        for name_of_child in names_of_children:
                child_completion = self._tally_completion_depth_first(
                    course_blocks[name_of_child], 
                    course_blocks 
                )
                completion_of_children += child_completion

        return completion_of_children


    def _bfsTraverseBlocks(self, course_blocks):
        root_name = course_blocks['root']
        course_nodes = course_blocks['blocks']

        traversal_queue = deque()
        traversal_queue.appendleft(course_nodes[root_name])

        current_block = None
        while len(traversal_queue) > 0:
            current_block = traversal_queue.pop()
            current_block_completion = current_block.get('completion', None)

            for child_name in current_block.get('children', []):
                traversal_queue.appendleft(course_nodes[child_name])
