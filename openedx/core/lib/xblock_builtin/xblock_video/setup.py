"""
Setup for the Video XBlock.
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
