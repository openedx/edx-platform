# lint-amnesty, pylint: disable=missing-module-docstring

from setuptools import find_packages, setup

XMODULES = [
    "book = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "customtag = xmodule.template_module:CustomTagDescriptor",
    "discuss = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "image = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "poll_question = xmodule.poll_module:PollDescriptor",
    "section = xmodule.backcompat_module:SemanticSectionDescriptor",
    "slides = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "videodev = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "custom_tag_template = xmodule.raw_module:RawDescriptor",
    "raw = xmodule.raw_module:RawDescriptor",
]
XBLOCKS = [
    "about = xmodule.html_module:AboutBlock",
    "annotatable = xmodule.annotatable_module:AnnotatableBlock",
    "chapter = xmodule.seq_module:SectionBlock",
    "conditional = xmodule.conditional_module:ConditionalBlock",
    "course = xmodule.course_module:CourseBlock",
    "course_info = xmodule.html_module:CourseInfoBlock",
    "error = xmodule.error_module:ErrorBlock",
    "hidden = xmodule.hidden_module:HiddenDescriptor",
    "html = xmodule.html_module:HtmlBlock",
    "library = xmodule.library_root_xblock:LibraryRoot",
    "library_content = xmodule.library_content_module:LibraryContentBlock",
    "library_sourced = xmodule.library_sourced_block:LibrarySourcedBlock",
    "lti = xmodule.lti_module:LTIBlock",
    "nonstaff_error = xmodule.error_module:NonStaffErrorBlock",
    "problem = xmodule.capa_module:ProblemBlock",
    "problemset = xmodule.seq_module:SequenceBlock",
    "randomize = xmodule.randomize_module:RandomizeBlock",
    "sequential = xmodule.seq_module:SequenceBlock",
    "split_test = xmodule.split_test_module:SplitTestBlock",
    "static_tab = xmodule.html_module:StaticTabBlock",
    "unit = xmodule.unit_block:UnitBlock",
    "vertical = xmodule.vertical_block:VerticalBlock",
    "video = xmodule.video_module:VideoBlock",
    "videoalpha = xmodule.video_module:VideoBlock",
    "videosequence = xmodule.seq_module:SequenceBlock",
    "word_cloud = xmodule.word_cloud_module:WordCloudBlock",
    "wrapper = xmodule.wrapper_module:WrapperBlock",
]
XBLOCKS_ASIDES = [
    'tagging_aside = cms.lib.xblock.tagging:StructuredTagsAside',
]

setup(
    name="XModule",
    version="0.1.2",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        'setuptools',
        'docopt',
        'capa',
        'path.py',
        'webob',
        'edx-opaque-keys>=0.4.0',
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
