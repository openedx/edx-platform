"""
Setup for discussion-forum XBlock.
"""


import os
from setuptools import find_packages, setup


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
            'discussion = xblock_discussion:DiscussionXBlock'
        ]
    },
    packages=find_packages(exclude=['tests.*']),
    package_data=package_data("xblock_discussion", ["static"]),
)
