from setuptools import setup, find_packages

setup(
    name="XModule",
    version="0.1",
    packages=find_packages(),
    install_requires=['distribute'],
    package_data={
        '': ['js/*']
    },

    # See http://guide.python-distribute.org/creation.html#entry-points
    # for a description of entry_points
    entry_points={
        'xmodule.v1': [
            "course = seq_module:SequenceDescriptor",
            "html = html_module:HtmlModuleDescriptor",
        ]
    }
)
