"""
Setup script for the Open edX package.
"""

from setuptools import setup

setup(
    name="Open edX",
    version="0.2",
    install_requires=['distribute'],
    requires=[],
    # NOTE: These are not the names we should be installing.  This tree should
    # be reorganized to be a more conventional Python tree.
    packages=[
        "openedx.core.djangoapps.user_api",
        "openedx.core.djangoapps.course_groups",
        "lms",
        "cms",
    ],
    entry_points={
        'openedx.user_partition_scheme': [
            'random = openedx.core.djangoapps.user_api.partition_schemes:RandomUserPartitionScheme',
            'cohort = openedx.core.djangoapps.course_groups.partition_scheme:CohortPartitionScheme',
        ],
    }
)
