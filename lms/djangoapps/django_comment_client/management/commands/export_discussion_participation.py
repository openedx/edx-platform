import csv
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.courses import get_course
from student.models import CourseEnrollment
from lms.lib.comment_client.user import User
import django_comment_client.utils as utils


class _Fields:
    USERNAME = u"username"
    EMAIL = u"email"
    FIRST_NAME = u"first_name"
    LAST_NAME = u"last_name"
    THREADS = u"num_threads"
    COMMENTS = u"num_comments"
    REPLIES = u"num_replies"
    UPVOTES = u"num_upvotes"
    FOLOWERS = u"num_thread_followers"
    COMMENTS_GENERATED = u"num_comments_generated"


def _make_social_stats(threads=0, comments=0, replies=0, upvotes=0, followers=0, comments_generated=0):
    return {
        _Fields.THREADS: threads,
        _Fields.COMMENTS: comments,
        _Fields.REPLIES: replies,
        _Fields.UPVOTES: upvotes,
        _Fields.FOLOWERS: followers,
        _Fields.COMMENTS_GENERATED: comments_generated,
    }


class Command(BaseCommand):
    args = "<course_id> <output_file_location>"

    row_order = [
        _Fields.USERNAME, _Fields.EMAIL, _Fields.FIRST_NAME, _Fields.LAST_NAME,
        _Fields.THREADS, _Fields.COMMENTS, _Fields.REPLIES,
        _Fields.UPVOTES, _Fields.FOLOWERS, _Fields.COMMENTS_GENERATED
    ]

    def _get_users(self, course_key):
        users = CourseEnrollment.users_enrolled_in(course_key)
        return {user.id: user for user in users}

    def _get_social_stats(self, course_key):
        return {
            int(user_id): data
            for user_id, data in User.all_social_stats(str(course_key)).iteritems()
        }

    def _merge_user_data_and_social_stats(self, userdata, social_stats):
        result = []
        for user_id, user in userdata.iteritems():
            user_record = {
                _Fields.USERNAME: user.username,
                _Fields.EMAIL: user.email,
                _Fields.FIRST_NAME: user.first_name,
                _Fields.LAST_NAME: user.last_name,
            }
            stats = social_stats.get(user_id, _make_social_stats())
            result.append(utils.merge_dict(user_record, stats))
        return result

    def _output(self, data, output_stream):
        csv_writer = csv.DictWriter(output_stream, self.row_order)
        csv_writer.writeheader()
        for row in sorted(data, key=lambda item: item['username']):
            to_write = {key: value for key, value in row.items() if key in self.row_order}
            csv_writer.writerow(to_write)

    def get_default_file_location(self, course_key):
        return utils.format_filename(
            "social_stats_{course}_{date:%Y_%m_%d_%H_%M_%S}.csv".format(course=course_key, date=datetime.utcnow())
        )

    def handle(self, *args, **options):
        if not args:
            raise CommandError("Course id not specified")
        if len(args) > 2:
            raise CommandError("Only one course id may be specifiied")
        raw_course_key = args[0]

        if len(args) == 1:
            output_file_location = self.get_default_file_location(raw_course_key)
        else:
            output_file_location = args[1]

        try:
            course_key = CourseKey.from_string(raw_course_key)
        except InvalidKeyError:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(raw_course_key)

        course = get_course(course_key)
        if not course:
            raise CommandError("Invalid course id: {}".format(course_key))

        users = self._get_users(course_key)
        social_stats = self._get_social_stats(course_key)
        merged_data = self._merge_user_data_and_social_stats(users, social_stats)

        self.stdout.write("Writing social stats to {}\n".format(output_file_location))
        with open(output_file_location, 'wb') as output_stream:
            self._output(merged_data, output_stream)

        self.stdout.write("Success!\n")