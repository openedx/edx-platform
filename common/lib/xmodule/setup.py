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
            "chapter = xmodule.seq_module:SequenceDescriptor",
            "course = xmodule.seq_module:SequenceDescriptor",
            "html = xmodule.html_module:HtmlDescriptor",
            "section = xmodule.translation_module:SemanticSectionDescriptor",
            "sequential = xmodule.seq_module:SequenceDescriptor",
            "vertical = xmodule.vertical_module:VerticalDescriptor",
            "problemset = xmodule.seq_module:SequenceDescriptor",
            "videosequence = xmodule.seq_module:SequenceDescriptor",
            "video = xmodule.video_module:VideoDescriptor",
        ]
    }
)
