"""
Setup for discussion-forum XBlock.
"""

from setuptools import find_packages, setup

from openedx.core.lib.xblock_builtin import package_data


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
