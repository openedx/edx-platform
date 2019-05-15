"""
Setup.py for safe_lxml.
"""
from __future__ import absolute_import

from setuptools import setup

setup(
    name="safe_lxml",
    version="1.0",
    packages=["safe_lxml"],
    install_requires=[
        "lxml",
        "defusedxml"
    ],
)
