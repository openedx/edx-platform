

import csv
import os

from django.core.management.base import BaseCommand, CommandError

from common.djangoapps.student.models import UserProfile


class Command(BaseCommand):
    help = """
    Sets or gets certificate restrictions for users
    from embargoed countries. (allow_certificate in
    userprofile)

    CSV should be comma delimited with double quoted entries.

        $ ... cert_restriction --import path/to/userlist.csv

    Export a list of students who have "allow_certificate" in
    userprofile set to True

        $ ... cert_restriction --output path/to/export.csv

    Enable a single user so she is not on the restricted list

        $ ... cert_restriction -e user

    Disable a single user so she is on the restricted list

        $ ... cert_restriction -d user

    """

    def add_arguments(self, parser):
        # This command can only take one of these arguments per run, this enforces that.
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-i', '--import',
                           metavar='IMPORT_FILE',
                           nargs='?',
                           help='CSV file to import, comma delimitted file with double-quoted entries')
        group.add_argument('-o', '--output',
                           metavar='EXPORT_FILE',
                           nargs='?',
                           help='CSV file to export')
        group.add_argument('-e', '--enable',
                           metavar='STUDENT',
                           nargs='?',
                           help='Enable a certificate for a single student')
        group.add_argument('-d', '--disable',
                           metavar='STUDENT',
                           nargs='?',
                           help='Disable a certificate for a single student')

    def handle(self, *args, **options):
        if options['output']:
            if os.path.exists(options['output']):
                raise CommandError("File {0} already exists".format(options['output']))
            disabled_users = UserProfile.objects.filter(allow_certificate=False)

            with open(options['output'], 'w') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for user in disabled_users:
                    csvwriter.writerow([user.user.username])
                    print('{} disabled users written'.format(len(disabled_users)))

        elif options['import']:
            if not os.path.exists(options['import']):
                raise CommandError("File {0} does not exist".format(options['import']))

            print("Importing students from {0}".format(options['import']))

            with open(options['import']) as csvfile:
                student_list = csv.reader(csvfile, delimiter=',', quotechar='"')
                students = [student[0] for student in student_list]

            if not students:
                raise CommandError("Unable to read student data from {0}".format(options['import']))

            update_cnt = UserProfile.objects.filter(user__username__in=students).update(allow_certificate=False)
            print('{} user(s) disabled out of {} in CSV file'.format(update_cnt, len(students)))

        elif options['enable']:
            print("Enabling {0} for certificate download".format(options['enable']))
            cert_allow = UserProfile.objects.get(user__username=options['enable'])
            cert_allow.allow_certificate = True
            cert_allow.save()

        elif options['disable']:
            print("Disabling {0} for certificate download".format(options['disable']))
            cert_allow = UserProfile.objects.get(user__username=options['disable'])
            cert_allow.allow_certificate = False
            cert_allow.save()
