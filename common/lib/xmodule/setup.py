from setuptools import setup, find_packages

setup(
    name="XModule",
    version="0.1",
    packages=find_packages(exclude=["tests"]),
    install_requires=['distribute'],
    package_data={
        'xmodule': ['js/module/*']
    },
    requires=[
        'capa',
        'mitxmako'
    ],

    # See http://guide.python-distribute.org/creation.html#entry-points
    # for a description of entry_points
    entry_points={
        'xmodule.v1': [
            "abtest = xmodule.abtest_module:ABTestDescriptor",
            "book = xmodule.translation_module:TranslateCustomTagDescriptor",
            "chapter = xmodule.seq_module:SequenceDescriptor",
            "course = xmodule.seq_module:SequenceDescriptor",
            "customtag = xmodule.template_module:CustomTagDescriptor",
            "discuss = xmodule.translation_module:TranslateCustomTagDescriptor",
            "html = xmodule.html_module:HtmlDescriptor",
            "image = xmodule.translation_module:TranslateCustomTagDescriptor",
            "problem = xmodule.capa_module:CapaDescriptor",
            "problemset = xmodule.vertical_module:VerticalDescriptor",
            "section = xmodule.translation_module:SemanticSectionDescriptor",
            "sequential = xmodule.seq_module:SequenceDescriptor",
            "slides = xmodule.translation_module:TranslateCustomTagDescriptor",
            "vertical = xmodule.vertical_module:VerticalDescriptor",
            "video = xmodule.video_module:VideoDescriptor",
            "videodev = xmodule.translation_module:TranslateCustomTagDescriptor",
            "videosequence = xmodule.seq_module:SequenceDescriptor",
        ]
    }
)
