import factory

from opaque_keys.edx.keys import UsageKey
from openedx.features.philu_courseware.models import CompetencyAssessmentRecord
from student.tests.factories import UserFactory


class CompetencyAssessmentRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CompetencyAssessmentRecord

    chapter_id = 'test-chapter'
    problem_id = UsageKey.from_string('block-v1:PUCIT+IT1+1+type@problem+block@7f1593ef300e4f569e26356b65d3b76b')
    problem_text = 'Test problem text'
    assessment_type = 'post'
    attempt = 1
    correctness = 'correct'
    choice_id = '1'
    choice_text = 'This is test choice'
    score = '1'
    user = factory.SubFactory(UserFactory)
    question_number = 1
