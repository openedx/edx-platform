from setuptools import find_packages, setup

XMODULES = [
    "book = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "chapter = xmodule.seq_module:SectionDescriptor",
    "conditional = xmodule.conditional_module:ConditionalDescriptor",
    "course = xmodule.course_module:CourseDescriptor",
    "customtag = xmodule.template_module:CustomTagDescriptor",
    "discuss = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "html = xmodule.html_module:HtmlDescriptor",
    "image = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "library_content = xmodule.library_content_module:LibraryContentDescriptor",
    "error = xmodule.error_module:ErrorDescriptor",
    "poll_question = xmodule.poll_module:PollDescriptor",
    "problem = xmodule.capa_module:CapaDescriptor",
    "problemset = xmodule.seq_module:SequenceDescriptor",
    "randomize = xmodule.randomize_module:RandomizeDescriptor",
    "split_test = xmodule.split_test_module:SplitTestDescriptor",
    "section = xmodule.backcompat_module:SemanticSectionDescriptor",
    "sequential = xmodule.seq_module:SequenceDescriptor",
    "slides = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "video = xmodule.video_module:VideoDescriptor",
    "videoalpha = xmodule.video_module:VideoDescriptor",
    "videodev = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "videosequence = xmodule.seq_module:SequenceDescriptor",
    "course_info = xmodule.html_module:CourseInfoDescriptor",
    "static_tab = xmodule.html_module:StaticTabDescriptor",
    "custom_tag_template = xmodule.raw_module:RawDescriptor",
    "about = xmodule.html_module:AboutDescriptor",
    "annotatable = xmodule.annotatable_module:AnnotatableDescriptor",
    "word_cloud = xmodule.word_cloud_module:WordCloudDescriptor",
    "hidden = xmodule.hidden_module:HiddenDescriptor",
    "raw = xmodule.raw_module:RawDescriptor",
    "lti = xmodule.lti_module:LTIDescriptor",
]
XBLOCKS = [
    "library = xmodule.library_root_xblock:LibraryRoot",
    "vertical = xmodule.vertical_block:VerticalBlock",
    "wrapper = xmodule.wrapper_module:WrapperBlock",
]
XBLOCKS_ASIDES = [
    'tagging_aside = cms.lib.xblock.tagging:StructuredTagsAside',
]

setup(
    name="XModule",
    version="0.1.1",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        'setuptools',
        'docopt',
        'capa',
        'path.py',
        'webob',
        'edx-opaque-keys>=0.4.0,<1.0.0',
    ],
    package_data={
        'xmodule': ['js/module/*'],
    },

    # See https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins
    # for a description of entry_points
    entry_points={
        'xblock.v1': XMODULES + XBLOCKS,
        'xmodule.v1': XMODULES,
        'xblock_asides.v1': XBLOCKS_ASIDES,
        'console_scripts': [
            'xmodule_assets = xmodule.static_content:main',
        ],
    },
)
