from django.core.management.base import BaseCommand, CommandError
import os
from optparse import make_option
from student.models import UserProfile
import csv


class Command(BaseCommand):

    help = """
    Sets or gets certificate restrictions for users
    from embargoed countries.

    Import a list of students to restrict certificate download
    by setting "allow_certificate" to True in userprofile:

        $ ... cert_restriction --import path/to/userlist.csv

    CSV should be comma delimited with double quoted entries.

    Export a list of students who have "allow_certificate" in
    userprofile set to True

        $ ... cert_restriction --export path/to/export.csv

    """

    option_list = BaseCommand.option_list + (
        make_option('-i', '--import',
                    metavar='IMPORT_FILE',
                    dest='import',
                    default=False,
                    help='csv file to import, comma delimitted file with '
                         'double-quoted entries'),
        make_option('-o', '--output',
                    metavar='EXPORT_FILE',
                    dest='output',
                    default=False,
                    help='csv file to export'),
        make_option('-e', '--enable',
                    metavar='STUDENT',
                    dest='enable',
                    default=False,
                    help="enable a single student's certificate"),
        make_option('-d', '--disable',
                    metavar='STUDENT',
                    dest='disable',
                    default=False,
                    help="disable a single student's certificate")
    )

    def handle(self, *args, **options):

        if options['output']:

            if os.path.exists(options['output']):
                raise CommandError("File {0} already exists".format(
                    options['output']))
            disabled_users = UserProfile.objects.filter(
                allow_certificate=False)

            with open(options['output'], 'w') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"',
                                       quoting=csv.QUOTE_MINIMAL)
                for user in disabled_users:
                    csvwriter.writerow([user.username])

        elif options['input']:

            if not os.path.exists(options['input']):
                raise CommandError("File {0} does not exist".format(
                    options['input']))

            print "Importing students from {0}".format(options['input'])

            students = None
            with open(options['input']) as csvfile:
                student_list = csv.reader(csvfile, delimiter=',',
                                          quotechar='"')
                students = [student[0] for student in student_list]
            if not students:
                raise CommandError(
                    "Unable to read student data from {0}".format(
                        options['input']))
            UserProfile.objects.filter(username__in=students).update(
                allow_certificate=False)

        elif options['enable']:

            print "Enabling {0} for certificate download".format(
                options['enable'])
            cert_allow = UserProfile.objects.get(user=options['enable'])
            cert_allow.allow_certificate = True
            cert_allow.save()

        elif options['disable']:

            print "Disabling {0} for certificate download".format(
                options['disable'])
            cert_allow = UserProfile.objects.get(user=options['disable'])
            cert_allow.allow_certificate = False
            cert_allow.save()
