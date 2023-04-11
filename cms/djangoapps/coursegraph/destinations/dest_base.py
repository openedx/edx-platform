class BaseCoursegraphDestination:
    @staticmethod
    def strip_branch_and_version(location):
        """
        Removes the branch and version information from a location.
        Args:
            location: an xblock's location.
        Returns: that xblock's location without branch and version information.
        """
        return location.for_branch(None)

    @staticmethod
    def get_course_last_published(course_key):
        """
        Approximately when was a course last published?

        We use the 'modified' column in the CourseOverview table as a quick and easy
        (although perhaps inexact) way of determining when a course was last
        published. This works because CourseOverview rows are re-written upon
        course publish.

        Args:
            course_key: a CourseKey

        Returns: The datetime the course was last published at, stringified.
            Uses Python's default str(...) implementation for datetimes, which
            is sortable and similar to ISO 8601:
            https://docs.python.org/3/library/datetime.html#datetime.date.__str__
        """
        # Import is placed here to avoid model import at project startup.
        from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

        approx_last_published = CourseOverview.get_from_id(course_key).modified
        return str(approx_last_published)
