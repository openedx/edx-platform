from setuptools import setup, find_packages

setup(
    name="Open edX",
    version="0.1",
    install_requires=['distribute'],
    requires=[],
    # NOTE: These are not the names we should be installing.  This tree should
    # be reorgnized to be a more conventional Python tree.
    packages=[
        "lms",
        "cms",
    ],
)
