# -*- coding: utf-8 -*-
#
# CME management command: dump userinfo to csv files for reporting

import csv
from datetime import datetime
from optparse import make_option
import sys
import tempfile

from django.core.management.base import BaseCommand, CommandError
from pytz import UTC

from certificates.models import GeneratedCertificate
from cme_registration.models import CmeUserProfile
from student.models import CourseEnrollment
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from shoppingcart.models import PaidCourseRegistration

from unidecode import unidecode

PROFILE_FIELDS = [
    ('user__profile__cmeuserprofile__last_name', 'Last Name'),
    ('user__profile__cmeuserprofile__middle_initial', 'Middle Initial'),
    ('user__profile__cmeuserprofile__first_name', 'First Name'),
    ('user__email', 'Email Address'),
    ('user__profile__cmeuserprofile__birth_date', 'Birth Date'),
    ('user__profile__cmeuserprofile__professional_designation', 'Professional Designation'),
    ('user__profile__cmeuserprofile__license_number', 'Professional License Number'),
    ('user__profile__cmeuserprofile__license_country', 'Professional License Country'),
    ('user__profile__cmeuserprofile__license_state', 'Professional License State'),
    ('user__profile__cmeuserprofile__physician_status', 'Physician Status'),
    ('user__profile__cmeuserprofile__patient_population', 'Patient Population'),
    ('user__profile__cmeuserprofile__specialty', 'Specialty'),
    ('user__profile__cmeuserprofile__sub_specialty', 'Sub Specialty'),
    ('user__profile__cmeuserprofile__affiliation', 'Stanford Medicine Affiliation'),
    ('user__profile__cmeuserprofile__sub_affiliation', 'Stanford Sub Affiliation'),
    ('user__profile__cmeuserprofile__stanford_department', 'Stanford Department'),
    ('user__profile__cmeuserprofile__sunet_id', 'SUNet ID'),
    ('user__profile__cmeuserprofile__other_affiliation', 'Other Affiliation'),
    ('user__profile__cmeuserprofile__job_title_position_untracked', 'Job Title or Position'),
    ('user__profile__cmeuserprofile__address_1', 'Address 1'),
    ('user__profile__cmeuserprofile__address_2', 'Address 2'),
    ('user__profile__cmeuserprofile__city_cme', 'City'),
    ('user__profile__cmeuserprofile__state', 'State'),
    ('user__profile__cmeuserprofile__postal_code', 'Postal Code'),
    ('user__profile__cmeuserprofile__county_province', 'County/Province'),
    ('user__profile__cmeuserprofile__country_cme', 'Country'),
    ('user__profile__cmeuserprofile__phone_number_untracked', 'Phone Number'),
    ('user__profile__cmeuserprofile__gender', 'Gender'),
    ('user__profile__cmeuserprofile__marketing_opt_in_untracked', 'Marketing Opt-In'),
    ('user__id', '')
]

REGISTRATION_FIELDS = [
    ('system_id_untracked', 'System ID'),
    ('line_cost', 'Fee Charged'),
    ('line_cost', 'Amount Paid'),
    ('reference_untracked', 'Reference'),
    ('dietary_restrictions_untracked', 'Dietary Restrictions'),
    ('marketing_source_untracked', 'Marketing Source'),
]

ORDER_FIELDS = [
    ('purchase_time', 'Date Registered'),
    ('bill_to_cardtype', 'Payment Type'),
    ('bill_to_ccnum', 'Reference Number'),
    (['bill_to_first', 'bill_to_last'], 'Paid By'),
]

CERTIFICATE_FIELDS = [
    ('credits_special_case', 'Credits Issued'),
    ('modified_date', 'Credit Date'),
    ('has_certificate_special_case', 'Certif'),
]

CME_SPECIFIC_ORDER = (
    PROFILE_FIELDS +
    REGISTRATION_FIELDS[0:1] +
    ORDER_FIELDS[0:1] +
    REGISTRATION_FIELDS[1:2] +
    ORDER_FIELDS[1:2] +
    REGISTRATION_FIELDS[2:3] +
    ORDER_FIELDS[2:3] +
    REGISTRATION_FIELDS[3:4] +
    ORDER_FIELDS[3:4] +
    REGISTRATION_FIELDS[4:] +
    CERTIFICATE_FIELDS
)


class Command(BaseCommand):
    help = """Export data required by Stanford SCCME Tracker Project to .csv file."""

    option_list = BaseCommand.option_list + (
        make_option(
            '-c',
            '--course',
            metavar='COURSE_ID',
            dest='course',
            default=False,
            help='The course id (e.g., CME/001/2013-2015) to select from.',
        ),
        make_option(
            '-d',
            '--code',
            metavar='COURSE_CODE',
            dest='code',
            default=False,
            help='The course code (e.g., 40490) that accreditors expect.',
        ),
        make_option(
            '-s',
            '--start',
            metavar='START_DATE',
            dest='start_date',
            default=False,
            help='The date to start collecting enrollment/completion events.',
        ),
        make_option(
            '-e',
            '--end',
            metavar='END_DATE',
            dest='end_date',
            default=False,
            help='The date to stop collecting enrollment/completion events.',
        ),
        make_option(
            '-o',
            '--outfile',
            metavar='OUTFILE',
            dest='outfile',
            default=False,
            help='The file path to which to write the output.',
        ),
    )

    def handle(self, *args, **options):
        course_id = options['course']
        course_code = options['code']
        start_date = datetime.strptime(options['start_date'], '%Y-%m-%d').replace(tzinfo=UTC)
        end_date = datetime.strptime(options['end_date'], '%Y-%m-%d').replace(tzinfo=UTC)
        outfile_name = options['outfile']
        verbose = int(options['verbosity']) > 1

        if not (course_id):
            raise CommandError('--course must be specified')

        try:
            course_id = CourseKey.from_string(course_id)
        except InvalidKeyError:
            course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)

        if outfile_name:
            outfile = open(outfile_name, 'wb')
        else:
            outfile = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
            outfile_name = outfile.name

        csv_fieldnames = [label for field, label in CME_SPECIFIC_ORDER if len(label) > 0]

        csvwriter = csv.DictWriter(outfile, fieldnames=csv_fieldnames, delimiter='\t', quoting=csv.QUOTE_ALL)
        csvwriter.writeheader()

        sys.stdout.write("Fetching enrolled students for {course}...".format(course=course_id))

        certificates, profiles, registrations, unpaid_registrations = self.query_database_for(course_id)

        registration_table = self.build_user_table(registrations)
        unpaid_registration_table = self.build_user_table(unpaid_registrations)
        certificate_table = self.build_user_table(certificates)

        sys.stdout.write(" done.\n")

        count = 0
        total = len(profiles)
        start = datetime.now(UTC)

        intervals = int(0.10 * total)
        if intervals > 100 and verbose:
            intervals = 101

        sys.stdout.write("Processing users")

        for profile in profiles:
            user_id = profile['user__id']
            self.print_progress(count, intervals, verbose)

            student_dict = {
                'Credits Issued': 0.0,  # XXX should be revisited when credit count functionality implemented
                'Certif': False,
            }

            for field, label in PROFILE_FIELDS:
                if 'untracked' not in field and len(label) > 0:
                    student_dict[label] = profile[field]

            registration = self.add_fields_to(student_dict, REGISTRATION_FIELDS, registration_table, user_id)

            if registration:
                self.add_fields_to(student_dict, ORDER_FIELDS, {user_id: registration.order}, user_id)

                #Registration order special case values
                if student_dict['Payment Type'] == 'Visa':
                    student_dict['Payment Type'] = 'VISA'

                if student_dict['Payment Type'] == 'MasterCard':
                    student_dict['Payment Type'] = 'MC'

            if 'Date Registered' not in student_dict:
                student_dict['Date Registered'] = unpaid_registration_table[user_id].created.strftime("%m/%d/%Y")

            certificate = self.add_fields_to(student_dict, CERTIFICATE_FIELDS, certificate_table, user_id)

            # If the user has received a certificate, adjust their credits issued and course completion flag.
            if student_dict['Credit Date']:
                student_dict['Credits Issued'] = 23.5
                student_dict['Certif'] = True

            student_dict['System ID'] = course_code

            try:
                if (
                        self.lies_between(student_dict['Date Registered'], start_date, end_date)
                        or
                        self.lies_between(student_dict['Credit Date'], start_date, end_date)
                ):
                    pass
                else:
                    continue
            except KeyError:
                continue

            for item in student_dict:
                student_dict[item] = self.preprocess(student_dict[item])

            csvwriter.writerow(student_dict)

            count += 1

        outfile.close()
        sys.stdout.write("Data written to {name}\n".format(name=outfile_name))

    def query_database_for(self, course_id):
        cme_profiles = CourseEnrollment.objects.select_related('user__profile__cmeuserprofile').filter(course_id=course_id).values(
            *[field for field, label in PROFILE_FIELDS if 'untracked' not in field]
        ).order_by('user__username')
        unpaid_registrations = CourseEnrollment.objects.filter(course_id=course_id)
        registrations = PaidCourseRegistration.objects.filter(status='purchased', course_id=course_id)
        certificates = GeneratedCertificate.objects.filter(course_id=course_id)
        return certificates, cme_profiles, registrations, unpaid_registrations

    def build_user_table(self, data_rows):
        table = {}

        for row in data_rows:
            table[getattr(row, 'user_id')] = row

        return table

    def add_fields_to(self, values, fields, table, user_id):
        try:
            raw_data = table[user_id]
        except KeyError:
            raw_data = None

        for field, label in fields:
            if label not in values:
                if type(field) is list:
                    values[label] = ' '.join([getattr(raw_data, f, '') for f in field])
                else:
                    values[label] = getattr(raw_data, field, '')

        return raw_data

    def lies_between(self, query_date, start, end):
        if type(query_date) is datetime:
            return start <= query_date and query_date < end
        else:
            return False

    def preprocess(self, value):
        if type(value) is datetime:
            value = value.strftime("%m/%d/%Y")

        value = unidecode(unicode(value))
        value = value.replace("_", " ")
        value = value.replace("\t", "")

        return value

    def print_progress(self, count, intervals, verbose):
        if count % intervals == 0:
            if verbose:
                diff = datetime.now(UTC) - start
                timeleft = diff * (total - count) / intervals
                hours, remainder = divmod(timeleft.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                sys.stdout.write(
                    "\n{count}/{total} completed ~{hours:02}:{minutes:02} remaining\n".format(
                        count=count,
                        total=total,
                        hours=hours,
                        minutes=minutes,
                    )
                )
                start = datetime.now(UTC)
            else:
                sys.stdout.write('.')
