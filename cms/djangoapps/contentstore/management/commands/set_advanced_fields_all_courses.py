"""
Script for updating an Advanced Setting across all courses.

This script is setup to only update the `modulestore` courses.
"""

import copy
import json
import logging

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.management import CommandError
from django.core.management.base import BaseCommand

from .utils import user_from_str
from ....contentstore.views.course import update_course_advanced_settings

from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Duraration:
        When running this against all courses it may take considerable more time because
        the course publishes out. This is due to the `update_course_advanced_settings` call.

    Invoke with:

        # Single Course
        # Set the following advanced settings:
        # `invitation_only` to `true`
        # `catalog_visilibilty` to `about`
        python manage.py cms --settings=devstack_docker set_advanced_fields_all_courses \
        --fields_json '{"invitation_only": {"value": "true"}}' --user edx@example.com --course course-v1:ORG+COURSENUMBER+COURSERUN --force-update-catalog-visibility-about # pylint: disable=line-too-long

        # All Courses
        # Set the following advanced settings:
        # `invitation_only` to `true`
        # `catalog_visilibilty` to `about`
        # `cerfificate_display_behavior` to `early_no_info`
        python manage.py cms --settings=devstack_docker set_advanced_fields_all_courses \
        --fields_json '{"invitation_only": {"value": "true"}, "certificates_display_behavior": {"value": "early_no_info"}}' --user edx@example.com --course course-v1:ORG+COURSENUMBER+COURSERUN --force-update-catalog-visibility-about # pylint: disable=line-too-long

        # All Courses
        # Set the following advanced settings:
        # `catalog_visilibilty` to `about`
        python manage.py cms --settings=devstack_docker set_advanced_fields_all_courses \
        --fields_json '{}' --user edx@example.com --course course-v1:ORG+COURSENUMBER+COURSERUN --force-update-catalog-visibility-about # pylint: disable=line-too-long
    """
    help = 'Set an advanced settings for all courses based on a json list of fields.'

    fields_json_help = '\
        Need to have a json list of "field_name": "<new value>" \
        { \
            "catalog_visibility": { \
                "value": "about" \
            }, \
            "certificates_display_behavior": { \
                "value": "early_no_info" \
            }, \
            "invitation_only": { \
                "value": "true" \
            } \
        }'
    user_help = '--user <email> required, needs to be a staff member'
    course_help = '--course <id> required, e.g. course-v1:ORG+COURSENUMBER+COURSERUN'
    force_update_catalog_visibility_about_help = '--force-update-catalog-visibility-about, To fix `There was an error loading this course` error when loading MFE learning this forces `catalog_visibility` from `none` to `about`.'  # pylint: disable=line-too-long
    limit_bulk_update_operation_help = '--limit-bulk-update-operation {0-N}'

    _force_update_catalog_visibility_about = False
    _updated_catalog_visilibity_about = []

    def add_arguments(self, parser):
        parser.add_argument('--fields_json',
                            dest='fields_json',
                            default=False,
                            required=True,
                            help=self.fields_json_help)
        parser.add_argument('--user',
                            dest='user_email',
                            default=False,
                            required=True,
                            help=self.user_help)
        parser.add_argument('--course',
                            dest='course_id',
                            default=False,
                            required=False,
                            help=self.course_help)
        parser.add_argument('--force-update-catalog-visibility-about',
                            dest='force_update_catalog_visibility_about',
                            action='store_true',
                            help=self.force_update_catalog_visibility_about_help)

        # WARNING
        # Limiting the all courses bulk advanced setting update here to avoid consuming all
        # server memory. Defaulting bulk operations to 150 courses but you can use this argument
        # to specify any value different than the default.
        parser.add_argument('--limit-bulk-update-operation',
                            dest='limit_bulk_update_operation',
                            default=150,
                            required=False,
                            help=self.limit_bulk_update_operation_help)

    def handle(self, *args, **options):
        """
        Execute the command
        """
        self._force_update_catalog_visibility_about = options.get(
            'force_update_catalog_visibility_about', False
        )
        try:
            update_fields = json.loads(options["fields_json"])
        except ValueError as err:
            raise CommandError("Invalid JSON object") from err

        # Update course(s) to push out `fields_json` of advanced setting changes.
        self._set_courses_advanced_fields(
            update_fields,
            options['user_email'],
            options['course_id'],
            int(options['limit_bulk_update_operation'])
        )

    def _set_courses_advanced_fields(self, update_fields, user_email, course_id, limit_bulk_update_operation):  # pylint: disable=line-too-long
        """
        Export all courses to target directory and return the list of courses which failed to export
        """

        try:
            user = user_from_str(user_email)
        except User.DoesNotExist:
            logger.warning(user_email + " user does not exist")  # lint-amnesty, pylint: disable=logging-not-lazy
            logger.warning("Can't update fields")
            return

        # Single Course
        if course_id:
            course_module = modulestore().get_course(CourseKey.from_string(course_id))

            revised_update_fields = self._force_catalog_visibility_about(
                update_fields, course_module
            )

            print(f"Applying revised_update_fields = {revised_update_fields} to course {course_id} using `{user}` user.\n")  # pylint: disable=line-too-long
            print("=" * 80)
            updated_data = update_course_advanced_settings(
                course_module, revised_update_fields, user
            )

            print("=" * 80)

            for field in revised_update_fields.keys():
                print(f"Updated data for course advanced settings `{field}` = {updated_data[field]}")  # pylint: disable=line-too-long
                print("=" * 80)

        # All Courses
        else:
            courses = modulestore().get_courses()
            course_ids = [x.id for x in courses]

            failed_update_advanced_fields_courses = []

            for course_id in course_ids[:limit_bulk_update_operation]:  # pylint: disable=redefined-argument-from-local
                try:
                    course_module = modulestore().get_course(CourseKey.from_string(str(course_id)))

                    revised_update_fields = self._force_catalog_visibility_about(
                        update_fields, course_module
                    )

                    print(f"Applying revised_update_fields = {revised_update_fields} to course {course_id} using `{user}` user.\n")  # pylint: disable=line-too-long
                    updated_data = update_course_advanced_settings(
                        course_module, revised_update_fields, user
                    )

                    print("=" * 80)

                    for field in revised_update_fields.keys():
                        print(f"Updated data for course advanced settings `{field}` = {updated_data[field]}")  # pylint: disable=line-too-long
                        print("=" * 80)

                except Exception as err:  # pylint: disable=broad-except
                    failed_update_advanced_fields_courses.append(str(course_id))
                    print("=" * 30 + f"> Oops, failed to update fields for {course_id}")
                    print("Error:")
                    print(err)

            print("=" * 80)
            print("=" * 30 + "> Reset fields summary")
            print(f"Total number of courses needed to update advanced fields: {len(courses)}")
            print(f"Limited the bulk update operation to {limit_bulk_update_operation} courses to avoid using all memory on server.")  # pylint: disable=line-too-long
            print(f"Total number of courses which failed to update advanced fields: {len(failed_update_advanced_fields_courses)}")  # pylint: disable=line-too-long
            print("List of updated advanced fields failed courses ids:")
            print("\n".join(failed_update_advanced_fields_courses))

            if self._force_update_catalog_visibility_about:
                print("List of updated courses ids `catalog_visibility` changes from `none` to `about`:")  # pylint: disable=line-too-long
                print("\n".join(self._updated_catalog_visilibity_about))

            print("=" * 80)

    def _force_catalog_visibility_about(self, update_fields, course_module):
        """
        Explicitly update `catalog_visilibility` = `none` to `about` to fix issue with
        `There was an error loading this course`.
        Details: https://discuss.openedx.org/t/how-to-programmatically-set-a-course-advanced-fields/8901/3  # pylint: disable=line-too-long

        Return fields to update with the following settings added.

        {
            "catalog_visibility": {
                "value": "about"
            }
        }
        """

        revised_update_fields = copy.deepcopy(update_fields)

        if hasattr(course_module, 'catalog_visibility') and getattr(course_module, 'catalog_visibility', 'none') == 'none':  # pylint: disable=line-too-long
            print(f"Found course `{course_module.id}` that has `catalog_visibility` set to `none`.")

            # Set `catalog_visibility`=`none` to `about` in `revised_update_fields` values.
            if self._force_update_catalog_visibility_about:
                try:
                    if hasattr(revised_update_fields, 'catalog_visibility'):
                        revised_update_fields['catalog_visibility']['value'] = 'about'
                    else:
                        revised_update_fields.update({
                            "catalog_visibility": {
                                "value": "about"
                            }
                        })
                except KeyError:
                    raise CommandError("Value error missing in `catalog_visibility` JSON object")  # lint-amnesty, pylint: disable=raise-missing-from

                print(
                    "Added { 'catalog_visibility': { 'value': 'about' } } to `revised_update_fields`, "  # pylint: disable=line-too-long
                    "to prevent `There was an error loading this course` in MFE Learning."
                )

                # Keep track of the courses that have changed `catalog_visibility` values from
                # `none` to `about`
                self._updated_catalog_visilibity_about.append(str(course_module.id))

        return revised_update_fields
