from setuptools import setup, find_packages

setup(
    name="edX Apps",
    version="0.1",
    install_requires=['distribute'],
    requires=[
        'xmodule',
    ],
    py_modules=['lms.xmodule_namespace', 'cms.xmodule_namespace'],
    # See http://guide.python-distribute.org/creation.html#entry-points
    # for a description of entry_points
    entry_points={
        'xblock.namespace': [
            'lms = lms.xmodule_namespace:LmsNamespace',
            'cms = cms.xmodule_namespace:CmsNamespace',
        ],
    }
)