"""
Setup for capa-problems XBlock.
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
    name='xblock-capa-problems',
    version='0.1',
    description='XBlock - CAPA Problems',
    install_requires=[
        'XBlock',
    ],
    entry_points={
        'xblock.v1': [
            'problem = xblock_capa_problems:CapaProblemsXBlock',
        ]
    },
    packages=find_packages(exclude=['tests.*']),
    package_data=package_data("xblock_capa_problems", ["static"]),
)
