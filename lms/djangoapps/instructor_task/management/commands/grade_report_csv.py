#!/usr/bin/python
"""
django management command: dump grades to csv files
for use by batch processes
"""
from courseware.courses import get_course_by_id
import requests
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run the task of student grade report of given course\n"
    help += "Usage: grade_report_csv -u instructor_email -p password course_id  base_url\n"

    option_list = BaseCommand.option_list + (
        make_option('-u',
                    '--user',
                    dest='user_email',
                    help="Existing user email address with access to edX demo course 'edX/DemoX/Demo_Course'"),
        make_option('-p',
                    '--password',
                    dest='password',
                    help="Password for provided user"),
    )

    def handle(self, *args, **options):

        print "args = ", args
        print "options = ",options
        if options['user_email'] is None or options['password'] is None:
            print self.help
            return

        if len(args) > 1:
            course_id = args[0]
            base_url = args[1]
        else:
            print self.help
            return

        course_key = None
        # parse out the course id into a coursekey
        try:
            course_key = CourseKey.from_string(course_id)
        # if it's not a new-style course key, parse it from an old-style
        # course key
        except InvalidKeyError:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        try:
            _course = get_course_by_id(course_key)
        except Exception as err:
            print "-----------------------------------------------------------------------------"
            print "Sorry, cannot find course with id {}".format(course_id)
            print "Got exception {}".format(err)
            print "Please provide a valid course ID"
            return

        user_email = options['user_email']
        user_password = options['password']
        client = requests.session()
        client.get(base_url)
        csrftoken = client.cookies['csrftoken']
        cookies = dict(client.cookies)

        try:
            user = User.objects.get(email=user_email)
            print "User with email '{0}' found on domain: {1}".format(user_email, base_url)
        except User.DoesNotExist:
            print "User with email '{0}' does not exist on domain: {1}".format(user_email, base_url)
            return

        # Log in the user
        login_url = base_url + '/login_ajax'
        headers = {"X-CSRFToken": csrftoken}
        payload = {'email': user.email, 'password': user_password}
        resp = client.post(login_url, headers=headers, data=payload, cookies=cookies)

        if resp.status_code == 200 and resp.json().get('success'):
            print "User '{0}' logged in successfully on {1}".format(user_email, login_url)
        else:
            print "User '{0}' failed to logged on {1} {2}".format(user_email, login_url, resp.__dict__)
            return



        print "-----------------------------------------------------------------------------"
        print "Computing grades for {}".format(course_id)
        grade_report_url = base_url + '/courses/' + course_id + '/instructor/api/calculate_grades_csv'
        response = client.get(grade_report_url)
        print response._content