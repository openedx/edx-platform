from setuptools import setup, find_packages

XMODULES = [
    "abtest = xmodule.abtest_module:ABTestDescriptor",
    "book = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "chapter = xmodule.seq_module:SequenceDescriptor",
    "combinedopenended = xmodule.combined_open_ended_module:CombinedOpenEndedDescriptor",
    "conditional = xmodule.conditional_module:ConditionalDescriptor",
    "course = xmodule.course_module:CourseDescriptor",
    "customtag = xmodule.template_module:CustomTagDescriptor",
    "discuss = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "html = xmodule.html_module:HtmlDescriptor",
    "image = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "error = xmodule.error_module:ErrorDescriptor",
    "peergrading = xmodule.peer_grading_module:PeerGradingDescriptor",
    "poll_question = xmodule.poll_module:PollDescriptor",
    "problem = xmodule.capa_module:CapaDescriptor",
    "problemset = xmodule.seq_module:SequenceDescriptor",
    "randomize = xmodule.randomize_module:RandomizeDescriptor",
    "section = xmodule.backcompat_module:SemanticSectionDescriptor",
    "sequential = xmodule.seq_module:SequenceDescriptor",
    "slides = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "timelimit = xmodule.timelimit_module:TimeLimitDescriptor",
    "vertical = xmodule.vertical_module:VerticalDescriptor",
    "video = xmodule.video_module:VideoDescriptor",
    "videoalpha = xmodule.video_module:VideoDescriptor",
    "videodev = xmodule.backcompat_module:TranslateCustomTagDescriptor",
    "videosequence = xmodule.seq_module:SequenceDescriptor",
    "discussion = xmodule.discussion_module:DiscussionDescriptor",
    "course_info = xmodule.html_module:CourseInfoDescriptor",
    "static_tab = xmodule.html_module:StaticTabDescriptor",
    "custom_tag_template = xmodule.raw_module:RawDescriptor",
    "about = xmodule.html_module:AboutDescriptor",
    "wrapper = xmodule.wrapper_module:WrapperDescriptor",
    "graphical_slider_tool = xmodule.gst_module:GraphicalSliderToolDescriptor",
    "annotatable = xmodule.annotatable_module:AnnotatableDescriptor",
    "foldit = xmodule.foldit_module:FolditDescriptor",
    "word_cloud = xmodule.word_cloud_module:WordCloudDescriptor",
    "hidden = xmodule.hidden_module:HiddenDescriptor",
    "raw = xmodule.raw_module:RawDescriptor",
    "crowdsource_hinter = xmodule.crowdsource_hinter:CrowdsourceHinterDescriptor",
    "lti = xmodule.lti_module:LTIModuleDescriptor",
]

setup(
    name="XModule",
    version="0.1",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        'distribute',
        'docopt',
        'capa',
        'path.py',
    ],
    package_data={
        'xmodule': ['js/module/*'],
    },

    # See http://guide.python-distribute.org/creation.html#entry-points
    # for a description of entry_points
    entry_points={
        'xblock.v1': XMODULES,
        'xmodule.v1': XMODULES,
        'console_scripts': [
            'xmodule_assets = xmodule.static_content:main',
        ],
    },
)
