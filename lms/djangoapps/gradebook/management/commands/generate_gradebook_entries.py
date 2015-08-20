"""
One-time data migration script -- shouldn't need to run it again
"""
import json
import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from courseware import grades
from gradebook.models import StudentGradebook
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import EdxJSONEncoder
from util.request import RequestMockWithoutMiddleware

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Creates (or updates) gradebook entries for the specified course(s) and/or user(s)
    """

    def handle(self, *args, **options):
        help = "Command to create or update gradebook entries"
        option_list = BaseCommand.option_list + (
            make_option(
                "-c",
                "--course_ids",
                dest="course_ids",
                help="List of courses for which to generate grades",
                metavar="first/course/id,second/course/id"
            ),
            make_option(
                "-u",
                "--user_ids",
                dest="user_ids",
                help="List of users for which to generate grades",
                metavar="1234,2468,3579"
            ),
        )

        course_ids = options.get('course_ids')
        user_ids = options.get('user_ids')

        # Get the list of courses from the system
        courses = modulestore().get_courses()

        # If one or more courses were specified by the caller, just use those ones...
        if course_ids is not None:
            filtered_courses = []
            for course in courses:
                if unicode(course.id) in course_ids.split(','):
                    filtered_courses.append(course)
            courses = filtered_courses

        for course in courses:
            users = CourseEnrollment.objects.users_enrolled_in(course.id)
            # If one or more users were specified by the caller, just use those ones...
            if user_ids is not None:
                filtered_users = []
                for user in users:
                    if str(user.id) in user_ids.split(','):
                        filtered_users.append(user)
                users = filtered_users

            # For each user...
            for user in users:
                request = RequestMockWithoutMiddleware().get('/')
                request.user = user
                grade_data = grades.grade(user, request, course)
                grade = grade_data['percent']
                grading_policy = course.grading_policy
                proforma_grade = grades.calculate_proforma_grade(grade_data, grading_policy)
                progress_summary = grades.progress_summary(user, request, course)
                try:
                    gradebook_entry = StudentGradebook.objects.get(user=user, course_id=course.id)
                    if (gradebook_entry.grade != grade or
                            gradebook_entry.proforma_grade != proforma_grade or
                            gradebook_entry.progress_summary != progress_summary or
                            gradebook_entry.grade_summary != grade_data or
                            gradebook_entry.grading_policy != grading_policy):
                        gradebook_entry.grade = grade
                        gradebook_entry.proforma_grade = proforma_grade
                        gradebook_entry.progress_summary = json.dumps(progress_summary, cls=EdxJSONEncoder)
                        gradebook_entry.grade_summary = json.dumps(grade_data, cls=EdxJSONEncoder)
                        gradebook_entry.grading_policy = json.dumps(grading_policy, cls=EdxJSONEncoder)
                        gradebook_entry.save()
                except StudentGradebook.DoesNotExist:
                    StudentGradebook.objects.create(
                        user=user,
                        course_id=course.id,
                        grade=grade,
                        proforma_grade=proforma_grade,
                        progress_summary=json.dumps(progress_summary, cls=EdxJSONEncoder),
                        grade_summary=json.dumps(grade_data, cls=EdxJSONEncoder),
                        grading_policy=json.dumps(grading_policy, cls=EdxJSONEncoder)
                    )
                log_msg = 'Gradebook entry created -- Course: {}, User: {}  (grade: {}, proforma_grade: {})'.format(course.id, user.id, grade, proforma_grade)
                print log_msg
                log.info(log_msg)
