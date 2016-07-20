# pylint: disable=missing-docstring

from django.core.management.base import BaseCommand

from request_cache.middleware import RequestCache
from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """
    Command to fetch courses that are using NumPy or matplotlib.pyplot in CAPA problems.
    """

    def handle(self, *args, **options):
        store = modulestore()
        courses_list = []

        course_ids = [course_summary.id for course_summary in store.get_course_summaries()]

        for course_id in course_ids:
            problems = store.get_items(course_id, qualifiers={'category': 'problem'})

            for problem in problems:
                if "numpy" in problem.data or "pyplot" in problem.data:
                    if course_id not in courses_list:
                        courses_list.append(course_id)

            RequestCache.clear_request_cache()

        import sys
        print >> sys.stderr, courses_list
