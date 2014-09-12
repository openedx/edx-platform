#!/usr/bin/python
#
# CME management command: dump userinfo to csv files for reporting

import csv
from datetime import datetime
from optparse import make_option
import sys
import tempfile

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from pytz import UTC

from certificates.models import GeneratedCertificate
from cme_registration.models import CmeUserProfile
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from shoppingcart.models import PaidCourseRegistration
from student.models import UserProfile


PROFILE_FIELDS = [
                  ('username', "Username"), # TODO: does this mess CME ingestion up? If so, drop; it's just for debug.
                  ('first_name', "First Name"),
                  ('middle_initial', "Middle Initial"),
                  ('last_name', "Last Name"),
                  ('email', "Email Address"),
                  ('birth_date', "Birth Date"),
                  ('professional_designation', "Professional Designation"),
                  ('license_number', "Professional License Number"),
                  ('license_countr', "Professional License Country"),
                  ('license_state', "Professional License State"),
                  ('physician_status', "Physician Status"),
                  ('patient_population', "Patient Population"),
                  ('specialty', 'Specialty'),
                  ('sub_specialty', "Sub Specialty"),
                  ('affiliation', "Stanford Medicine Affiliation"),
                  ('sub_affiliation', "Stanford Sub Affiliation"),
                  ('stanford_department', "Stanford Department"),
                  ('sunet_id', "SUNet ID"),
                  ('other_affiliation', "Other Affiliation"),
                  ('job_title_position_untracked', 'Job Title or Position'), # Untracked
                  ('address_1', 'Address 1'),
                  ('address_2', 'Address 2'),
                  ('city', 'City'),
                  ('state', 'State'),
                  ('county_province', 'County/Province'),
                  ('country', 'Country'),
                  ('phone_number_untracked', 'Phone Number'), # Untracked
                  ('gender', 'Gender'),
                  ('marketing_opt_in_fixme', 'Marketing Opt-In'), # FIXME: where do we get this?
                 ]

class Command(BaseCommand):
    help = """Export data required by Stanford SCCME Tracker Project to .csv file."""

    option_list = BaseCommand.option_list + (
        make_option('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course',
                    default=False,
                    help='The course id (e.g., CME/001/2013-2015) to select from. Mutually exclusive with "--all"'),
        make_option('-a', '--all',
                    dest='all',
                    default=False,
                    help='Request all users dumped for all courses; mutually exclusive with "--course"'),
        make_option('-o', '--outfile',
                    metavar='OUTFILE',
                    dest='outfile',
                    default=False,
                    help='The file path to which to write the output.'),
    )


    def handle(self, *args, **options):

        course_id = options['course']
        do_all_courses = options['all']
        outfile_name = options['outfile']
        verbose = int(options['verbosity']) > 1

        if do_all_courses:
            raise CommandError('--all is not currently implemented; please use --course')
        if not (do_all_courses or course_id):
            raise CommandError('--course and --all are mutually exclusive')
        elif (do_all_courses and course_id):
            raise CommandError('One of --coure or --all must be given')

        try:
            course_id = CourseKey.from_string(course_id)
        except InvalidKeyError:
            course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

        outfile = None
        if outfile_name:
            outfile = open(outfile_name, 'wb')
        else:
            outfile = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
            outfile_name = outfile.name

        csv_fieldnames = [x[1] for x in PROFILE_FIELDS]
        csv_fieldnames.extend(['System ID', 'Date Registered', 'Fee Charged', 'Payment Type', 'Amount Paid',
                               'Reference Number', 'Reference', 'Paid By', 'Dietary Restrictions',
                               'Marketing Source', 'Credits Issued', 'Credit Date', 'Certif'])
        csvwriter = csv.DictWriter(outfile, fieldnames=csv_fieldnames, delimiter='\t', quoting=csv.QUOTE_ALL)
        csvwriter.writeheader()

        sys.stdout.write("Fetching enrolled students for {course}...".format(course=course_id))
        enrolled_students = User.objects.filter(courseenrollment__course_id=course_id).prefetch_related("groups").order_by('username')
        sys.stdout.write(" done.\n")

        count = 0
        total = enrolled_students.count()
        start = datetime.now(UTC)
        intervals = int(0.10 * total)
        if intervals > 100 and verbose:
            intervals = 101
        sys.stdout.write("Processing users")

        for student in enrolled_students:

            student_dict = {'Credits Issued': 0.0,
                            'Credit Date': None,
                            'Certif': False
                           } 

            count += 1
            if count % intervals == 0:
                if verbose:
                    diff = datetime.now(UTC) - start
                    timeleft = diff * (total - count) / intervals
                    hours, remainder = divmod(timeleft.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    sys.stdout.write("\n{count}/{total} completed ~{hours:02}:{minutes:02} remaining\n".format(count=count, total=total, hours=hours, minutes=minutes))
                    start = datetime.now(UTC)
                else:
                    sys.stdout.write('.')

            usr_profile = UserProfile.objects.get(user=student)
            cme_profiles = CmeUserProfile.objects.filter(user=student)
            registration = PaidCourseRegistration.objects.filter(user=student, status='purchased', course_id=course_id)
            registration_order = None
            cert_info = GeneratedCertificate.objects.filter(user=student, course_id=course_id)

            # Learner Profile Data
            if cme_profiles:
                cme_profile = cme_profiles[0]

            for field, label in PROFILE_FIELDS:
                fieldvalue = getattr(cme_profile, field, '') or getattr(usr_profile, field, '') or getattr(student, field, '')
                student_dict[label] = fieldvalue

            # Learner Registration Data
            if registration:
                registration = registration[0]
                registration_order = registration.order
            student_dict['Date Registered'] = getattr(registration_order, 'purchase_time', '')
            student_dict['System ID'] = '' # FIXME what is this?
            student_dict['Reference'] = '' # FIXME what is this?
            student_dict['Dietary Restrictions'] = '' # Untracked
            student_dict['Marketing Source'] = '' # Untracked
            student_dict['Fee Charged'] = getattr(registration, 'line_cost', '') # FIXME how are these different?
            student_dict['Amount Paid'] = getattr(registration, 'line_cost', '') # FIXME how are these different?
            student_dict['Payment Type'] = getattr(registration_order, 'bill_to_cardtype', '')
            student_dict['Reference Number'] = getattr(registration_order, 'bill_to_ccnum', '')
            student_dict['Paid By'] = ' '.join((getattr(registration_order, 'bill_to_first', ''), 
                                                getattr(registration_order, 'bill_to_last', '')))

            # Learner Credit Data
            if cert_info:
                cert_info = cert_info[0]
            cert_status = getattr(cert_info, 'status', '')
            student_dict['Credit Date'] = getattr(cert_info, 'created_date', '')
            student_dict['Certif'] = (cert_status == 'downloadable')
            if cert_status in ('downloadable', 'generating'):
                student_dict['Credits Issued'] = 30.0  # FIXME: should retrieve from course def.

            # DEBUG output, replace with csvwriter 
            #outfile.write("\n{d}\n".format(d=student_dict))
            csvwriter.writerow(student_dict)

#            import pdb; pdb.set_trace()
#
#        writer = csv.writer(fp, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
#        writer.writerow(datatable['header'])
#        for datarow in datatable['data']:
#            encoded_row = [unicode(s).encode('utf-8') for s in datarow]
#            writer.writerow(encoded_row)


        outfile.close()
        sys.stdout.write("Data written to {name}\n".format(name=outfile_name))
