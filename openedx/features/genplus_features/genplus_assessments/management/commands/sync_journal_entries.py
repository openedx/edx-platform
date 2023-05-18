import json
from lxml import etree
from django.test import RequestFactory
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import UsageKey, CourseKey
from collections import defaultdict
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from openedx.features.course_experience.utils import get_course_outline_block_tree
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.courseware.user_state_client import DjangoXBlockUserStateClient
from lms.djangoapps.courseware.models import StudentModule

from openedx.features.genplus_features.genplus.models import Student, JournalPost
from openedx.features.genplus_features.genplus.constants import JournalTypes
from openedx.features.genplus_features.genplus_learning.models import Unit
from openedx.features.genplus_features.genplus_assessments.utils import build_problem_list, get_problem_attributes
from openedx.features.genplus_features.genplus_assessments.constants import ProblemTypes, JOURNAL_STYLE


class Command(BaseCommand):
    help = 'Sync journal entries from course'

    def handle(self, *args, **options):
        user = get_user_model().objects.get(username='lms_worker')
        units = Unit.objects.all()
        store = modulestore()
        user_state_client = DjangoXBlockUserStateClient()

        for unit in units:
            course_id = unit.course.id
            skill = unit.skill if unit else None
            print(f"===============Course ID: {course_id}===================")
            usage_key = store.make_course_usage_key(course_id)
            with store.bulk_operations(course_id):
                course_blocks = get_course_blocks(user, usage_key)
                for _, _, block_key in build_problem_list(course_blocks, usage_key):
                    # Chapter and sequential blocks are filtered out since they include state
                    # which isn't useful for this report.
                    if block_key.block_type in ('course', 'sequential', 'chapter', 'vertical'):
                        continue

                    if not block_key.block_type == 'problem':
                        continue

                    block = store.get_item(block_key)
                    generated_report_data = defaultdict(list)
                    if not hasattr(block, 'is_journal_entry'):
                        continue
                    if not block.is_journal_entry:
                        continue

                    print(f"===============Journal Block found===================")
                    if hasattr(block, 'generate_report_data'):
                        try:
                            user_state_iterator = user_state_client.iter_all_for_block(
                                block_key)
                            for username, state in block.generate_report_data(user_state_iterator):
                                generated_report_data[username].append(state)
                        except NotImplementedError:
                            pass

                    student_list = list(generated_report_data.keys())
                    problem_attributes = get_problem_attributes(block.data, block_key)
                    for username in student_list:
                        try:
                            try:
                                student_module = StudentModule.objects.get(
                                    student__username=username,
                                    course_id=course_id,
                                    module_state_key=block_key,
                                )
                            except StudentModule.DoesNotExist:
                                student_module = None
                                print(f"===============Student module not found for user {username} and course {course_id} ===================")

                            student = Student.objects.filter(gen_user__user__username=username).first()
                            user_states = generated_report_data.get(username)
                            if problem_attributes['problem_type'] == ProblemTypes.JOURNAL and user_states:
                                for user_state in user_states:
                                    defaults = {
                                        'skill': skill,
                                        'journal_type': JournalTypes.STUDENT_POST,
                                        'title': user_state['Question'],
                                        'description': json.dumps(json.loads(JOURNAL_STYLE.format(user_state['Answer']), strict=False)),
                                        'is_editable': False
                                    }
                                    if student_module:
                                        defaults['created'] = student_module.created
                                        defaults['modified'] = student_module.modified

                                    obj, created = JournalPost.objects.update_or_create(
                                        uuid=user_state['Answer ID'],
                                        student=student,
                                        defaults=defaults
                                    )
                                    if created:
                                        print(f"===============Added Journal Entry===================")
                                    else:
                                        if student_module:
                                            JournalPost.objects.filter(uuid=user_state['Answer ID'], student=student).update(modified=student_module.modified)
                                        print(f"===============Updated Journal Entry===================")
                        except Exception as ex:
                            self.stdout.write(self.style.ERROR(str(ex)))

        self.stdout.write(self.style.SUCCESS('DONE!!'))
