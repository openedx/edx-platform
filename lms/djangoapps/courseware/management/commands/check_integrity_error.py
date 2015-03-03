"""
Script for testing IntegrityError exception raised on multiple concurrent
POST requests
"""
import concurrent.futures
import requests
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from lms.djangoapps.courseware.models import StudentModule


DEFAULT_WORKERS = 50
DEFAULT_REQUESTS = 5


class Command(BaseCommand):
    """
    Test IntegrityError exception raised on multiple concurrent POST requests
    """
    help = "Test IntegrityError exception raised on multiple concurrent POST requests\n" \
           "Usage: check_integrity_error -u <user_email> -p <password>\n"
    option_list = BaseCommand.option_list + (
        make_option('-u',
                    '--user',
                    dest='user_email',
                    help="Existing user email address with access to edX demo course 'edX/DemoX/Demo_Course'"),
        make_option('-p',
                    '--password',
                    dest='password',
                    help="Password for provided user"),
        make_option('-r',
                    '--requests',
                    dest='requests',
                    help="Number of concurrent requests for 'save_user_state' on demo video of edX demo course"),
        )

    def handle(self, *args, **options):
        """
        Execute the command
        """
        if options['user_email'] is None or options['password'] is None:
            print self.help
            return

        # Get user logged in on domain
        live_server_url = "http://localhost:8000"
        user_email = options['user_email']
        user_password = options['password']
        if options['requests'] is None:
            total_requests = DEFAULT_REQUESTS
        else:
            total_requests = int(options['requests'])

        client = requests.session()
        # Retrieve the CSRF token first
        client.get(live_server_url)     # sets cookie
        csrftoken = client.cookies['csrftoken']
        cookies = dict(client.cookies)

        try:
            user = User.objects.get(email=user_email)
            print "User with email '{0}' found on domain: {1}".format(user_email, live_server_url)
        except User.DoesNotExist:
            print "User with email '{0}' does not exist on domain: {1}".format(user_email, live_server_url)
            return

        # Log in the user
        login_url = live_server_url + '/login_ajax'
        headers = {"X-CSRFToken": csrftoken}
        payload = {'email': user.email, 'password': user_password}
        resp = client.post(login_url, headers=headers, data=payload, cookies=cookies)

        if resp.status_code == 200 and resp.json().get('success'):
            print "User '{0}' logged in successfully on {1}".format(user_email, login_url)
        else:
            print "User '{0}' failed to logged on {1}".format(user_email, login_url)
            return

        # Prepare POST request for 'save_user_state' on edX demo course 'edX/DemoX/Demo_Course'
        demo_course_video_url = live_server_url + "/courses/edX/DemoX/Demo_Course/xblock/" \
                                                  "i4x:;_;_edX;_DemoX;_video;_0b9e39477cf34507a7a48f74be381fdd/" \
                                                  "handler/xmodule_handler/save_user_state"
        payload = {'saved_video_position': "00:00:10"}

        # Clear previously added user's entry in StudentModule for video modules
        StudentModule.objects.filter(student_id=user.id, module_type='video').delete()

        # Method for sending POST request for 'save_user_state' on edX demo course 'edX/DemoX/Demo_Course'
        def fetch(part):
            print "sending request number: {0}".format(part)
            response = client.post(demo_course_video_url, headers=headers, data=payload, cookies=cookies)
            return response

        resp_500 = 0
        if not total_requests:
            total_requests = DEFAULT_REQUESTS
        with concurrent.futures.ThreadPoolExecutor(max_workers=DEFAULT_WORKERS) as executor:
            # Start the load operations and mark each future with its request number
            future_to_url = {executor.submit(fetch, number): number for number in range(total_requests)}
            for future in concurrent.futures.as_completed(future_to_url):
                request_number = future_to_url[future]
                try:
                    data = future.result()
                    if data.status_code == 500:
                        resp_500 += 1
                except Exception as exc:
                    resp_500 += 1
                    print('%r generated an exception: %s' % (request_number, exc))
                else:
                    print('Response of request# %r :%s' % (request_number, data))

        user_student_module_video_entry = StudentModule.objects.filter(student_id=user.id, module_type='video').count()

        print "=" * 80
        print u"----- Summary of requests on 'save_user_state' for IntegrityError -----"
        print u"-> Total number of concurrent requests for 'save_user_state': {0}".format(total_requests)
        print u"-> Total number of requests with server error (IntegrityError: 500): {0}/{1}".format(
            resp_500, total_requests)
        print u"-> User '{0}' entry count of StudentModule for video modules: {1}".format(
            user_email, user_student_module_video_entry)
        print "=" * 80
