from setuptools import setup, find_packages

setup(
    name="edX LMS",
    version="0.1",
    install_requires=['distribute'],
    requires=[
        'xmodule',
    ],

    # See http://guide.python-distribute.org/creation.html#entry-points
    # for a description of entry_points
    entry_points={
        'xmodule.namespace': [
            'lms = lms.xmodule_namespace:LmsNamespace'
        ],
    }
)