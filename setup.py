"""
Setup script for the Open edX package.
"""

from setuptools import setup

setup(
    name="Open edX",
    version="0.3",
    install_requires=["distribute"],
    requires=[],
    # NOTE: These are not the names we should be installing.  This tree should
    # be reorganized to be a more conventional Python tree.
    packages=[
        "openedx.core.djangoapps.course_groups",
        "openedx.core.djangoapps.user_api",
        "lms",
        "cms",
    ],
    entry_points={
        "openedx.course_view_type": [
            "ccx = lms.djangoapps.ccx.plugins:CcxCourseViewType",
            "edxnotes = lms.djangoapps.edxnotes.plugins:EdxNotesCourseViewType",
            "instructor = lms.djangoapps.instructor.views.instructor_dashboard:InstructorDashboardViewType",
        ],
        "openedx.user_partition_scheme": [
            "random = openedx.core.djangoapps.user_api.partition_schemes:RandomUserPartitionScheme",
            "cohort = openedx.core.djangoapps.course_groups.partition_scheme:CohortPartitionScheme",
        ],
    }
)
