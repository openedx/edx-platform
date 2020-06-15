from datetime import datetime
from logging import getLogger

from django.core.management.base import BaseCommand
from pytz import utc

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.assessment.constants import ORA_BLOCK_TYPE
from openedx.features.assessment.helpers import auto_score_ora, can_auto_score_ora
from openedx.features.philu_utils.utils import get_anonymous_user
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

log = getLogger(__name__)


class Command(BaseCommand):
    help = """
        Auto Score ORA assesment for On Demand Course if learner has completed all the necessary steps i-e 
        submitted their responses, assess required peers responses and finally own assessment if required, if that 
        learner ends up in a waiting queue after 2 weeks of response submission this command will auto-score the
        learner ORA assessment for those users. 
    """

    def handle(self, *args, **options):

        courses = CourseOverview.objects.filter(self_paced=True)

        for course in courses:
            enrollments = CourseEnrollment.objects.filter(course_id=course.id, is_active=True)

            for enrollment in enrollments:

                today = datetime.now(utc).date()
                delta_days = today - enrollment.created.date()
                current_module = (delta_days.days / 7) + 1
                user = enrollment.user

                if current_module < 3:
                    log.info('Current module is less than 3')
                    continue
                else:
                    max_module = 1

                    course_chapters = modulestore().get_items(
                        course.id,
                        qualifiers={'category': 'course'}
                    )
                    for index_chapter, chapter in enumerate(course_chapters[0].children):
                        if max_module < current_module:
                            sequentials = modulestore().get_item(chapter)
                            for index_sequential, sequential in enumerate(sequentials.children):
                                verticals = modulestore().get_item(sequential)
                                for index_vertical, vertical in enumerate(verticals.children):
                                    vertical_blocks = modulestore().get_item(vertical)
                                    for index_block, block in enumerate(vertical_blocks.children):
                                        if (block.block_type == ORA_BLOCK_TYPE and
                                                can_auto_score_ora(enrollment, course, block, index_chapter)):
                                            anonymous_user = get_anonymous_user(user, course.id)
                                            auto_score_ora(course.id, unicode(block), anonymous_user)

                        max_module = max_module + 1
