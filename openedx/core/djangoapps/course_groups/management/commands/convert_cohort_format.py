"""
Converts the old cohort_config format to the new one.
"""
from django.core.management import BaseCommand
from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """
    Command to convert settings in cohort_config to ones that can be translated by
    the lazy converter.

    For the solutions devstack, which used different property names.

    It appears the only change that needs to be made is to change 'inline_discussions_cohorting_default'
    to 'always_cohort_inline_discussions'. Every other difference can be ignored benignly.
    """
    help = 'Revert the multiple cohorts feature.'

    def handle(self, *args, **options):
        store = modulestore()
        for course in store.get_courses():
            if course.cohort_config:
                print "Updating affected course: %s" % unicode(course.location)
                if 'inline_discussions_cohorting_default' in course.cohort_config:
                    course.cohort_config['always_cohort_inline_discussions'] = course.cohort_config[
                        'inline_discussions_cohorting_default'
                    ]
                inlines = course.cohort_config.get('cohorted_inline_discussions', [])
                course_discussions = course.cohort_config.get('cohorted_course_wide_discussions', [])
                if inlines or course_discussions:
                    course.cohort_config['cohorted_discussions'] = inlines + course_discussions
                store.update_item(course, None)
                print "%s updated." % unicode(course.location)
