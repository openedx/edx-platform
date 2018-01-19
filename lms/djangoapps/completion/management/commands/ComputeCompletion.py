from collections import deque

from django.core.management.base import BaseCommand, CommandError
from django.http import HttpRequest

from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.course_api.blocks.api import get_blocks
from openedx.core.lib.celery.task_utils import emulate_http_request
from opaque_keys.edx.locator import CourseLocator
from django.test.client import RequestFactory
from openedx.features.course_experience.views.course_outline import get_course_outline_block_tree

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from student.tests.factories import UserFactory

class Command(BaseCommand):

#emulate_http_request in task_utils.py
#get_request_or_stub
    def handle(self, *args, **options):
        course_name = 'course-v1:Sandro+cs141+Spring2018'
        course_name = 'course-v1:wert+qw4tqw4t+qertqert'
        course_usage_key = self._create_course_usage_key(course_name)

        user = UserFactory.create(
            username="staff",
            email="staff@example.com"
            )
        site = SiteFactory.create()

        with emulate_http_request(site, user) as request:
            import cProfile
            # print "== get_blocks =="
            # import pudb; pu.db
            # cProfile.runctx('get_blocks(request, course_usage_key, user=user, requested_fields=[\'completion\', \'children\'])', globals(), locals())

            blocks = get_blocks(
                request, 
                course_usage_key,
                user=user,
                requested_fields=['completion', 'children']
            )

            # print "== _traverseBlocks =="
            # cProfile.runctx('self._traverseBlocks(blocks)', globals(), locals())
            # self._bfsTraverseBlocks(blocks)
            cProfile.runctx('self._recursiveComputeCompletion(blocks)', globals(), locals())
            # self._recursiveComputeCof a courseompletion(blocks)

    def _create_course_usage_key(self, course_name):
        course_key = CourseKey.from_string(course_name)
        return modulestore().make_course_usage_key(course_key)

    def _bfsTraverseBlocks(self, blocks):
        root_name = blocks['root']
        course_nodes = blocks['blocks']

        traversal_queue = deque()
        traversal_queue.appendleft(course_nodes[root_name])

        current_block = None
        while len(traversal_queue) > 0:
            current_block = traversal_queue.pop()
            current_block_completion = current_block.get('completion', None)

            # print current_block['id']
            for child_name in current_block.get('children', []):
                traversal_queue.appendleft(course_nodes[child_name])


    def _recursiveComputeCompletion(self, blocks):
        root_name = blocks['root']
        course_nodes = blocks['blocks']
        # print "Number of course_blocks: %d" % (len(course_nodes)) 

        course_completion = self._dfsComputeCompletion(
            course_nodes[root_name],
            course_nodes 
        )

        # print "Number of completed blocks: %f" % (course_completion)

    def _dfsComputeCompletion(self, current_block, course_blocks):

        names_of_children = current_block.get('children', None)
        completion_at_current_block = 0.0

        if names_of_children:

            for name_of_child in names_of_children:
                child_completion = self._dfsComputeCompletion(
                    course_blocks[name_of_child], 
                    course_blocks 
                )
                completion_at_current_block += child_completion

        else:
            completion_at_current_block = current_block.get('completion', 0.0)

        return completion_at_current_block
