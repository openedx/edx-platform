"""Setup for discussion-forum XBlock."""

import os
from setuptools import setup


def package_data(pkg, root_list):
    """Generic function to find package_data for `pkg` under `root`."""
    data = []
    for root in root_list:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='xblock-discussion',
    version='0.1',
    description='XBlock - Discussion Forum',
    packages=[
        'discussion_forum'
    ],
    install_requires=[
        'XBlock',
    ],
    entry_points={
        'xblock.v1': [
            'discussion-forum = discussion_forum:DiscussionXBlock',
            'discussion-course = discussion_forum:DiscussionCourseXBlock'
        ]
    },
    package_data=package_data("discussion_forum", ["static"]),
)
