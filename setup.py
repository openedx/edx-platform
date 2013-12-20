#!/usr/bin/env python

"""
Install Selenium page objects for acceptance and end-to-end tests.
"""

from setuptools import setup

VERSION = '0.0.1'
DESCRIPTION = "Selenium page objects for edx-platform"

setup(
    name='edx-selenium-pages',
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
    packages=['edxapp_selenium_pages']
)
