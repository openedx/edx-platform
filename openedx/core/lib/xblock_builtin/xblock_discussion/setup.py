"""
Setup for discussion-forum XBlock.
"""

import os
from setuptools import setup


def package_data(pkg, root_list):
    """
    Generic function to find package_data for `pkg` under `root`.
    """
    data = []
    for root in root_list:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='xblock-discussion',
    version='0.1',
    description='XBlock - Discussion',
    install_requires=[
        'XBlock',
    ],
    entry_points={
        'xblock.v1': [
            'discussion = xblock_discussion:DiscussionXBlock',
            # Alias "discussion-forum" entry point to the same XBlock.
            # This is necessary to ensure backward compatibility for courses
            # containing instances of the solutions-specific inline DiscussionXBlock,
            # which was removed in favor of the implementation provided in this package.
            'discussion-forum = xblock_discussion:DiscussionXBlock'
        ]
    },
    package_data=package_data("xblock_discussion", ["static"]),
)
