from setuptools import setup, find_packages

setup(
    name="XModule",
    version="0.1",
    packages=find_packages(),
    install_requires=['distribute'],
    entry_points={
        'xmodule.v1': [
            "Course = seq_module:CourseModuleDescriptor",
            "Chapter = seq_module:ChapterModuleDescriptor",
        ]
    }
)
