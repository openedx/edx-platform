from __future__ import absolute_import
from setuptools import setup

setup(
    name="chem",
    version="0.3.0",
    packages=["chem"],
    install_requires=[
        "pyparsing==2.2.0",
        "numpy",
        "scipy",
        "nltk",
        "markupsafe",  # Should be replaced by other utilities. See LEARNER-5853 for more details.
    ],
)
