"""
Management command to backfill default course tabs for all courses. This command is essentially for
when a new default tab is added and we need to update all existing courses. Any new courses will pick
up the new tab automatically via course creation and the CourseTabList.initialize_default method.
People updating to Nutmeg release should run this command as part of the upgrade process.

This should be invoked from the Studio process.

Note: This command will not fail due to updates, but can encounter errors and will log those out.
Search for the error message to detect any issues.
"""
import logging

from django.core.management.base import BaseCommand

from xmodule.tabs import CourseTabList
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Invoke with:
        python manage.py cms backfill_course_tabs
    """
    help = (
        'Backfill default course tabs for all courses. This command is essentially for when a new default '
        'tab is added and we need to update all existing courses. Any new courses will pick up the new '
        'tab automatically via course creation and the CourseTabList.initialize_default method.'
    )

    def handle(self, *args, **options):
        """
        Gathers all course keys in the modulestore and updates the course tabs
        if there are any new default course tabs. Else, makes no updates.
        """
        store = modulestore()
        course_keys = sorted(
            (course.id for course in store.get_course_summaries()),
            key=str  # Different types of CourseKeys can't be compared without this.
        )
        logger.info(f'{len(course_keys)} courses read from modulestore.')

        for course_key in course_keys:
            course = store.get_course(course_key, depth=1)
            existing_tabs = {tab.type for tab in course.tabs}
            CourseTabList.initialize_default(course)
            new_tabs = {tab.type for tab in course.tabs}

            if existing_tabs != new_tabs:
                # This will trigger the Course Published Signal which is necessary to update
                # the corresponding Course Overview
                logger.info(f'Updating tabs for {course_key}.')
                try:
                    store.update_item(course, ModuleStoreEnum.UserID.mgmt_command)
                    logger.info(f'Successfully updated tabs for {course_key}.')
                except Exception as err:  # pylint: disable=broad-except
                    logger.exception(err)
                    logger.error(f'Course {course_key} encountered an Exception while trying to update.')
