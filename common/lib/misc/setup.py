"""Installer for edx-platform/common/lib/misc."""

from setuptools import setup

setup(
    name="edx-common-lib-misc",
    version="0.1",
    packages=[
        "misc",
    ],
    install_requires=[
        "glob2",
    ],
)
