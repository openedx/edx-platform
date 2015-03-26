"""
Transfer Student Management Command
"""
from django.db import transaction
from opaque_keys.edx.keys import CourseKey
from optparse import make_option
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from shoppingcart.models import CertificateItem
from track.management.tracked_command import TrackedCommand


class TransferStudentError(Exception):
    """Generic Error when handling student transfers."""
    pass


class Command(TrackedCommand):
    """Management Command for transferring students from one course to new courses."""
    help = """
    This command takes two course ids as input and transfers
    all students enrolled in one course into the other.  This will
    remove them from the first class and enroll them in the specified
    class(es) in the same mode as the first one. eg. honor, verified,
    audit.

    example:
        # Transfer students from the old demoX class to a new one.
        manage.py ... transfer_students -f edX/Open_DemoX/edx_demo_course -t edX/Open_DemoX/new_demoX

        # Transfer students from old course to new, with original certificate items.
        manage.py ... transfer_students -f edX/Open_DemoX/edx_demo_course -t edX/Open_DemoX/new_demoX -c true

        # Transfer students from the old demoX class into two new classes.
        manage.py ... transfer_students -f edX/Open_DemoX/edx_demo_course
            -t edX/Open_DemoX/new_demoX,edX/Open_DemoX/edX_Insider

    """

    option_list = TrackedCommand.option_list + (
        make_option('-f', '--from',
                    metavar='SOURCE_COURSE',
                    dest='source_course',
                    help='The course to transfer students from.'),
        make_option('-t', '--to',
                    metavar='DEST_COURSE_LIST',
                    dest='dest_course_list',
                    help='The new course(es) to enroll the student into.'),
        make_option('-c', '--transfer-certificates',
                    metavar='TRANSFER_CERTIFICATES',
                    dest='transfer_certificates',
                    help="If True, try to transfer certificate items to the new course.")
    )

    @transaction.commit_manually
    def handle(self, *args, **options):  # pylint: disable=unused-argument
        source_key = CourseKey.from_string(options.get('source_course', ''))
        dest_keys = []
        for course_key in options.get('dest_course_list', '').split(','):
            dest_keys.append(CourseKey.from_string(course_key))

        if not source_key or not dest_keys:
            raise TransferStudentError(u"Must have a source course and destination course specified.")

        tc_option = options.get('transfer_certificates', '')
        transfer_certificates = ('true' == tc_option.lower()) if tc_option else False
        if transfer_certificates and len(dest_keys) != 1:
            raise TransferStudentError(u"Cannot transfer certificate items from one course to many.")

        source_students = User.objects.filter(
            courseenrollment__course_id=source_key
        )

        for user in source_students:
            with transaction.commit_on_success():
                print("Moving {}.".format(user.username))
                # Find the old enrollment.
                enrollment = CourseEnrollment.objects.get(
                    user=user,
                    course_id=source_key
                )

                # Move the Student between the classes.
                mode = enrollment.mode
                old_is_active = enrollment.is_active
                CourseEnrollment.unenroll(user, source_key, skip_refund=True)
                print(u"Unenrolled {} from {}".format(user.username, unicode(source_key)))

                for dest_key in dest_keys:
                    if CourseEnrollment.is_enrolled(user, dest_key):
                        # Un Enroll from source course but don't mess
                        # with the enrollment in the destination course.
                        msg = u"Skipping {}, already enrolled in destination course {}"
                        print(msg.format(user.username, unicode(dest_key)))
                    else:
                        new_enrollment = CourseEnrollment.enroll(user, dest_key, mode=mode)

                        # Un-enroll from the new course if the user had un-enrolled
                        # form the old course.
                        if not old_is_active:
                            new_enrollment.update_enrollment(is_active=False, skip_refund=True)

                        if transfer_certificates:
                            self._transfer_certificate_item(source_key, enrollment, user, dest_keys, new_enrollment)

    @staticmethod
    def _transfer_certificate_item(source_key, enrollment, user, dest_keys, new_enrollment):
        """ Transfer the certificate item from one course to another.

        Do not use this generally, since certificate items are directly associated with a particular purchase.
        This should only be used when a single course to a new location. This cannot be used when transferring
        from one course to many.

        Args:
            source_key (str): The course key string representation for the original course.
            enrollment (CourseEnrollment): The original enrollment to move the certificate item from.
            user (User): The user to transfer the item for.
            dest_keys (list): A list of course key strings to transfer the item to.
            new_enrollment (CourseEnrollment): The new enrollment to associate the certificate item with.

        Returns:
            None

        """
        try:
            certificate_item = CertificateItem.objects.get(
                course_id=source_key,
                course_enrollment=enrollment
            )
        except CertificateItem.DoesNotExist:
            print(u"No certificate for {}".format(user))
            return

        certificate_item.course_id = dest_keys[0]
        certificate_item.course_enrollment = new_enrollment
