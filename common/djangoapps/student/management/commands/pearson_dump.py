from optparse import make_option
from json import dump
from datetime import datetime

from django.core.management.base import BaseCommand

from student.models import TestCenterRegistration


class Command(BaseCommand):

    args = '<output JSON file>'
    help = """
    Dump information as JSON from TestCenterRegistration tables, including username and status.
    """

    option_list = BaseCommand.option_list + (
        make_option('--course_id',
                    action='store',
                    dest='course_id',
                    help='Specify a particular course.'),
        make_option('--exam_series_code',
                    action='store',
                    dest='exam_series_code',
                    default=None,
                    help='Specify a particular exam, using the Pearson code'),
        make_option('--accommodation_pending',
                    action='store_true',
                    dest='accommodation_pending',
                    default=False,
                    ),
    )

    def handle(self, *args, **options):
        if len(args) < 1:
            outputfile = datetime.utcnow().strftime("pearson-dump-%Y%m%d-%H%M%S.json")
        else:
            outputfile = args[0]

        # construct the query object to dump:
        registrations = TestCenterRegistration.objects.all()
        if 'course_id' in options and options['course_id']:
            registrations = registrations.filter(course_id=options['course_id'])
        if 'exam_series_code' in options and options['exam_series_code']:
            registrations = registrations.filter(exam_series_code=options['exam_series_code'])

        # collect output:
        output = []
        for registration in registrations:
            if 'accommodation_pending' in options and options['accommodation_pending'] and not registration.accommodation_is_pending:
                continue
            record = {'username': registration.testcenter_user.user.username,
                      'email': registration.testcenter_user.email,
                      'first_name': registration.testcenter_user.first_name,
                      'last_name': registration.testcenter_user.last_name,
                      'client_candidate_id': registration.client_candidate_id,
                      'client_authorization_id': registration.client_authorization_id,
                      'course_id': registration.course_id,
                      'exam_series_code': registration.exam_series_code,
                      'accommodation_request': registration.accommodation_request,
                      'accommodation_code': registration.accommodation_code,
                      'registration_status': registration.registration_status(),
                      'demographics_status': registration.demographics_status(),
                      'accommodation_status': registration.accommodation_status(),
                      }
            if len(registration.upload_error_message) > 0:
                record['registration_error'] = registration.upload_error_message
            if len(registration.testcenter_user.upload_error_message) > 0:
                record['demographics_error'] = registration.testcenter_user.upload_error_message
            if registration.needs_uploading:
                record['needs_uploading'] = True

            output.append(record)

        # dump output:
        with open(outputfile, 'w') as outfile:
            dump(output, outfile, indent=2)
