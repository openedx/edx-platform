"""
Setup for the Video XBlock.
"""

from setuptools import find_packages, setup

from openedx.core.lib.xblock_builtin import package_data


setup(
    name='xblock-video',
    version='0.1',
    description='XBlock - Videos',
    install_requires=[
        'XBlock',
    ],
    entry_points={
        'xblock.v1': [
            'video = xblock_video:VideoXBlock',
            'videoalpha = xblock_video:VideoXBlock',
        ]
    },
    packages=find_packages(exclude=['tests.*']),
    package_data=package_data("xblock_video", ["static"]),
)
