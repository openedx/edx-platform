#!/usr/bin/env python

"""
Install bok-choy page objects for acceptance and end-to-end tests.
"""

from setuptools import setup

VERSION = '0.0.1'
DESCRIPTION = "Bok-choy page objects for edx-platform"

setup(
    name='edxapp-pages',
    version=VERSION,
    author='edX',
    url='http://github.com/edx/edx-platform',
    description=DESCRIPTION,
    license='AGPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance'
    ],
    packages=['edxapp_pages', 'edxapp_pages.lms', 'edxapp_pages.studio']
)
