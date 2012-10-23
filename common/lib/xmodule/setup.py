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
    ],

    # See http://guide.python-distribute.org/creation.html#entry-points
    # for a description of entry_points
    entry_points={
        'xmodule.v1': [
            "abtest = xmodule.abtest_module:ABTestDescriptor",
            "book = xmodule.backcompat_module:TranslateCustomTagDescriptor",
            "chapter = xmodule.seq_module:SequenceDescriptor",
            "course = xmodule.course_module:CourseDescriptor",
            "customtag = xmodule.template_module:CustomTagDescriptor",
            "discuss = xmodule.backcompat_module:TranslateCustomTagDescriptor",
            "html = xmodule.html_module:HtmlDescriptor",
            "image = xmodule.backcompat_module:TranslateCustomTagDescriptor",
            "error = xmodule.error_module:ErrorDescriptor",
            "problem = xmodule.capa_module:CapaDescriptor",
            "problemset = xmodule.seq_module:SequenceDescriptor",
            "section = xmodule.backcompat_module:SemanticSectionDescriptor",
            "sequential = xmodule.seq_module:SequenceDescriptor",
            "slides = xmodule.backcompat_module:TranslateCustomTagDescriptor",
            "vertical = xmodule.vertical_module:VerticalDescriptor",
            "video = xmodule.video_module:VideoDescriptor",
            "videodev = xmodule.backcompat_module:TranslateCustomTagDescriptor",
            "videosequence = xmodule.seq_module:SequenceDescriptor",
            "discussion = xmodule.discussion_module:DiscussionDescriptor",
        ]
    }
)
