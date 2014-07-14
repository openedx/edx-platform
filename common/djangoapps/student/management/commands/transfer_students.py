from optparse import make_option
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from shoppingcart.models import CertificateItem
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class Command(BaseCommand):
    help = """
    This command takes two course ids as input and transfers
    all students enrolled in one course into the other.  This will
    remove them from the first class and enroll them in the second
    class in the same mode as the first one. eg. honor, verified,
    audit.

    example:
        # Transfer students from the old demoX class to a new one.
        manage.py ... transfer_students -f edX/Open_DemoX/edx_demo_course -t edX/Open_DemoX/new_demoX
    """

    option_list = BaseCommand.option_list + (
        make_option('-f', '--from',
                    metavar='SOURCE_COURSE',
                    dest='source_course',
                    help='The course to transfer students from.'),
        make_option('-t', '--to',
                    metavar='DEST_COURSE',
                    dest='dest_course',
                    help='The new course to enroll the student into.'),
    )

    def handle(self, *args, **options):
        source_key = SlashSeparatedCourseKey.from_deprecated_string(options['source_course'])
        dest_key = SlashSeparatedCourseKey.from_deprecated_string(options['dest_course'])

        source_students = User.objects.filter(
            courseenrollment__course_id=source_key
        )

        for user in source_students:
            if CourseEnrollment.is_enrolled(user, dest_key):
                # Un Enroll from source course but don't mess
                # with the enrollment in the destination course.
                CourseEnrollment.unenroll(user, source_key)
                print("Unenrolled {} from {}".format(user.username, source_key.to_deprecated_string()))
                msg = "Skipping {}, already enrolled in destination course {}"
                print(msg.format(user.username, dest_key.to_deprecated_string()))
                continue

            print("Moving {}.".format(user.username))
            # Find the old enrollment.
            enrollment = CourseEnrollment.objects.get(
                user=user,
                course_id=source_key
            )

            # Move the Student between the classes.
            mode = enrollment.mode
            old_is_active = enrollment.is_active
            CourseEnrollment.unenroll(user, source_key)
            new_enrollment = CourseEnrollment.enroll(user, dest_key, mode=mode)

            # Unenroll from the new coures if the user had unenrolled
            # form the old course.
            if not old_is_active:
                new_enrollment.update_enrollment(is_active=False)

            if mode == 'verified':
                try:
                    certificate_item = CertificateItem.objects.get(
                        course_id=source_key,
                        course_enrollment=enrollment
                    )
                except CertificateItem.DoesNotExist:
                    print("No certificate for {}".format(user))
                    continue

                certificate_item.course_id = dest_key
                certificate_item.course_enrollment = new_enrollment
                certificate_item.save()
