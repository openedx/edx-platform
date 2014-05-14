"""Django management command to force certificate generation"""
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from pdfgen.certificate import CertificatePDF
from xmodule.modulestore import Location
#from resource import setrlimit, RLIMIT_NOFILE


def check_course_id(course_id):
    """Check course_id."""
    match = Location.COURSE_ID_RE.match(course_id)
    if match is None:
        raise CommandError(
            "{} is not of form ORG/COURSE/NAME".format(course_id)
        )


class Command(BaseCommand):
    args = "<create, delete, report or publish> <course_id>"
    help = """Certificate PDF command."""

    option_list = BaseCommand.option_list + (
        make_option(
            '-n', '--noop',
            action='store_true',
            dest='noop',
            default=False,
            help="Print but do not anything."),
        make_option(
            '-u', '--user',
            metavar='<USERNAME or EMAIL>',
            dest='username',
            default=False,
            help='The username or email address for whom grading'
                 'and certification should be requested'),
        make_option(
            '-d', '--debug',
            action="store_true",
            dest='debug',
            default=False,
            help='Print for debugging'),
        make_option(
            '-i', '--include-prefix',
            metavar='INCLUDE-FIlE-PREFIX',
            dest='prefix',
            default="",
            help='prefix that include file.'),
        make_option(
            '-x', '--exclude-file',
            metavar='EXCLUDE-FILE',
            dest='exclude',
            default=None,
            help='file-path that include username or email list.')
    )

    def handle(self, *args, **options):
        user = options['username']
        debug = options['debug']
        noop = options['noop']
        prefix = options['prefix']
        exclude = options['exclude']

        if len(args) != 2:
            self.print_help("manage.py", "create_certs")
            raise CommandError("course_id or operation is not specified.")

        if prefix and exclude is not None:
            raise CommandError("-i option and -x option are not specified at the same time.")

        #setrlimit(RLIMIT_NOFILE, (fd, fd))
        operation, course_id = args
        check_course_id(course_id)
        certpdf = CertificatePDF(user, course_id, debug, noop, prefix, exclude)

        if operation == "create":
            certpdf.create()
        elif operation == "delete":
            certpdf.delete()
        elif operation == "report":
            certpdf.report()
        elif operation == "publish":
            certpdf.publish()
        else:
            self.print_help("manage.py", "create_certs")
            raise CommandError('Invalid operation.')
