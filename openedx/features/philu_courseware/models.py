from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import UsageKeyField

from student.models import CourseEnrollment

from .constants import (
    COMPETENCY_ASSESSMENT_DEFAULT_PROBLEMS_COUNT,
    COMPETENCY_ASSESSMENT_TYPE_CHOICES,
    CORRECT_ASSESSMENT_KEY,
    CORRECTNESS_CHOICES,
    PRE_ASSESSMENT_KEY
)


class CompetencyAssessmentManager(models.Manager):
    def revert_user_post_assessment_attempts(self, user, problem_id):
        post_assessment_records = self.get_queryset().filter(problem_id=problem_id, user=user, assessment_type='post')
        delete_result = post_assessment_records.delete()
        deleted_records_count = delete_result[0]
        return deleted_records_count

    def get_score(self, user, chapter_id):
        """
        Return competency assessments scores of user in chapter

        :param user: user
        :param chapter_id: chapter url_name.
        :return: assessments score dictionary
        """

        pre_assessment_attempted = None
        pre_assessment_score = post_assessment_score = attempted_pre_assessments = attempted_post_assessments = 0

        query_format = """
            SELECT MAX(`id`) AS `id`, COUNT(`assessment_type`) AS `assessments_count`, `assessment_type`, `correctness`
            FROM `philu_courseware_competencyassessmentrecord`
            WHERE `id` IN (
                SELECT MAX(`id`) FROM `philu_courseware_competencyassessmentrecord`
                WHERE `chapter_id` = '{chapter_id}' and `user_id` = {user_id}
                GROUP BY `problem_id`, `question_number`
            ) GROUP BY `correctness`, `assessment_type`
        """

        assessment_records = self.raw(query_format.format(chapter_id=chapter_id, user_id=user.id))

        """
            Sample result of upper query. This Query will return results of problems from latest attempt
            for both "Pre" and "Post" assessments. All attempts are saved in our table and we are concerned only with the
            latest one, hence sub query provides us the latest attempt of all problems

            |  id   | assessment_count | assessment_type   |  correctness  |
            +-------+------------------+-------------------+---------------+
            |  231  |         4        |       post        |   correct     |
            |  229  |         4        |       pre         |   correct     |
            |  232  |         1        |       post        |   incorrect   |
            |  233  |         1        |       pre         |   incorrect   |
        """

        for assessment in assessment_records:
            if assessment.assessment_type == PRE_ASSESSMENT_KEY:
                pre_assessment_attempted = True
                if assessment.correctness == CORRECT_ASSESSMENT_KEY:
                    pre_assessment_score = assessment.assessments_count
                attempted_pre_assessments += assessment.assessments_count

            else:
                if assessment.correctness == CORRECT_ASSESSMENT_KEY:
                    post_assessment_score = assessment.assessments_count
                attempted_post_assessments += assessment.assessments_count

        return {
            'pre_assessment_score': pre_assessment_score,
            'post_assessment_score': post_assessment_score,
            'pre_assessment_attempted': pre_assessment_attempted,
            'all_pre_assessment_attempted': attempted_pre_assessments == COMPETENCY_ASSESSMENT_DEFAULT_PROBLEMS_COUNT,
            'all_post_assessment_attempted': attempted_post_assessments == COMPETENCY_ASSESSMENT_DEFAULT_PROBLEMS_COUNT,
        }


class CompetencyAssessmentRecord(TimeStampedModel):
    chapter_id = models.TextField(max_length=255)
    problem_id = UsageKeyField(max_length=255)
    problem_text = models.TextField(null=False)
    assessment_type = models.CharField(max_length=4, choices=COMPETENCY_ASSESSMENT_TYPE_CHOICES)

    attempt = models.IntegerField()
    correctness = models.CharField(max_length=9, choices=CORRECTNESS_CHOICES)
    # It stores comma separated choice ids for example choice_1,choice_2,choice_3
    choice_id = models.CharField(max_length=255)
    choice_text = models.TextField()
    score = models.FloatField()
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    question_number = models.IntegerField(default=None, blank=True, null=True)

    objects = CompetencyAssessmentManager()

    def __unicode__(self):
        return '{problem}, question({question_number}), {username}, {assessment_type}, attempt({attempt})'.format(
            problem=self.problem_id,
            username=self.user.username,
            assessment_type=self.assessment_type,
            attempt=self.attempt,
            question_number=self.question_number
        )


class CourseEnrollmentMeta(models.Model):
    course_enrollment = models.OneToOneField(CourseEnrollment, related_name='course_enrollment_meta',
                                             related_query_name='course_enrollment_meta', on_delete=models.CASCADE)
    program_uuid = models.UUIDField(null=True, verbose_name=_('Program UUID'))
