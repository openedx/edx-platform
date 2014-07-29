# encoding: utf-8
"""
Modulestore configuration for test cases.
"""

from uuid import uuid4
from django.test import TestCase
from django.contrib.auth.models import User
from xmodule.contentstore.django import _CONTENTSTORE
from xmodule.modulestore.django import modulestore, clear_existing_modulestores
from xmodule.modulestore import ModuleStoreEnum
from collections import namedtuple
import datetime
import pytz
from xmodule.tabs import CoursewareTab, CourseInfoTab, StaticTab, DiscussionTab, ProgressTab, WikiTab


def mixed_store_config(data_dir, mappings):
    """
    Return a `MixedModuleStore` configuration, which provides
    access to both Mongo- and XML-backed courses.

    `data_dir` is the directory from which to load XML-backed courses.
    `mappings` is a dictionary mapping course IDs to modulestores, for example:

        {
            'MITx/2.01x/2013_Spring': 'xml',
            'edx/999/2013_Spring': 'default'
        }

    where 'xml' and 'default' are the two options provided by this configuration,
    mapping (respectively) to XML-backed and Mongo-backed modulestores..
    """
    draft_mongo_config = draft_mongo_store_config(data_dir)
    xml_config = xml_store_config(data_dir)
    split_mongo = split_mongo_store_config(data_dir)

    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.mixed.MixedModuleStore',
            'OPTIONS': {
                'mappings': mappings,
                'stores': [
                    draft_mongo_config['default'],
                    split_mongo['default'],
                    xml_config['default'],
                ]
            }
        }
    }
    return store


def draft_mongo_store_config(data_dir):
    """
    Defines default module store using DraftMongoModuleStore.
    """

    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': data_dir,
        'render_template': 'edxmako.shortcuts.render_to_string'
    }

    store = {
        'default': {
            'NAME': 'draft',
            'ENGINE': 'xmodule.modulestore.mongo.draft.DraftModuleStore',
            'DOC_STORE_CONFIG': {
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore{0}'.format(uuid4().hex[:5]),
            },
            'OPTIONS': modulestore_options
        }
    }

    return store


def split_mongo_store_config(data_dir):
    """
    Defines split module store.
    """
    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': data_dir,
        'render_template': 'edxmako.shortcuts.render_to_string',
        # ??? does this & draft need xblock_mixins?
    }

    store = {
        'default': {
            'NAME': 'draft',
            'ENGINE': 'xmodule.modulestore.split_mongo.split_draft.DraftVersioningModuleStore',
            'DOC_STORE_CONFIG': {
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore{0}'.format(uuid4().hex[:5]),
            },
            'OPTIONS': modulestore_options
        }
    }

    return store


def xml_store_config(data_dir):
    """
    Defines default module store using XMLModuleStore.
    """
    store = {
        'default': {
            'NAME': 'xml',
            'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
            'OPTIONS': {
                'data_dir': data_dir,
                'default_class': 'xmodule.hidden_module.HiddenDescriptor',
            }
        }
    }

    return store


# used to create course subtrees in ModuleStoreTestCase.create_test_course
# adds to self properties w/ the given block_id which hold the UsageKey for easy retrieval.
# fields is a dictionary of keys and values. sub_tree is a collection of BlockInfo
BlockInfo = namedtuple('BlockInfo', 'block_id, category, fields, sub_tree')
default_block_info_tree = [
    BlockInfo(
        'chapter_x', 'chapter', {}, [
            BlockInfo(
                'sequential_x1', 'sequential', {}, [
                    BlockInfo(
                        'vertical_x1a', 'vertical', {}, [
                            BlockInfo('problem_x1a_1', 'problem', {}, []),
                            BlockInfo('problem_x1a_2', 'problem', {}, []),
                            BlockInfo('problem_x1a_3', 'problem', {}, []),
                            BlockInfo('html_x1a_1', 'html', {}, []),
                        ]
                    )
                ]
            )
        ]
    ),
    BlockInfo(
        'chapter_y', 'chapter', {}, [
            BlockInfo(
                'sequential_y1', 'sequential', {}, [
                    BlockInfo(
                        'vertical_y1a', 'vertical', {}, [
                            BlockInfo('problem_y1a_1', 'problem', {}, []),
                            BlockInfo('problem_y1a_2', 'problem', {}, []),
                            BlockInfo('problem_y1a_3', 'problem', {}, []),
                        ]
                    )
                ]
            )
        ]
    )
]
# equivalent to toy course in xml
TOY_BLOCK_INFO_TREE = [
    BlockInfo(
        'Overview', "chapter", {"display_name" : "Overview"}, [
            BlockInfo(
                "Toy_Videos", "videosequence", {
                    "xml_attributes": {"filename": ["", None]}, "display_name": "Toy Videos", "format": "Lecture Sequence"
                }, [
                    BlockInfo(
                        "secret:toylab", "html", {
                            "data": "<b>Lab 2A: Superposition Experiment</b>\n\n<<<<<<< Updated upstream\n<p>Isn't the toy course great?</p>\n\n<p>Let's add some markup that uses non-ascii characters.\nFor example, we should be able to write words like encyclop&aelig;dia, or foreign words like fran&ccedil;ais.\nLooking beyond latin-1, we should handle math symbols:  &pi;r&sup2 &le; &#8734.\nAnd it shouldn't matter if we use entities or numeric codes &mdash; &Omega; &ne; &pi; &equiv; &#937; &#8800; &#960;.\n</p>\n=======\n<p>Isn't the toy course great? — &le;</p>\n>>>>>>> Stashed changes\n",
                            "xml_attributes": { "filename" : [  "html/secret/toylab.xml", "html/secret/toylab.xml" ] },
                            "display_name" : "Toy lab"
                        }, []
                    ),
                    BlockInfo(
                        "toyjumpto", "html", {
                            "data" : "<a href=\"/jump_to_id/vertical_test\">This is a link to another page and some Chinese 四節比分和七年前</a> <p>Some more Chinese 四節比分和七年前</p>\n",
                            "xml_attributes": { "filename" : [  "html/toyjumpto.xml", "html/toyjumpto.xml" ] }
                        }, []),
                    BlockInfo(
                        "toyhtml", "html", {
                            "data" : "<a href='/static/handouts/sample_handout.txt'>Sample</a>",
                            "xml_attributes" : { "filename" : [  "html/toyhtml.xml", "html/toyhtml.xml" ] }
                        }, []),
                    BlockInfo(
                        "nonportable", "html", {
                            "data": "<a href=\"/static/foo.jpg\">link</a>\n",
                            "xml_attributes" : { "filename" : [  "html/nonportable.xml", "html/nonportable.xml" ] }
                        }, []),
                    BlockInfo(
                        "nonportable_link", "html", {
                            "data": "<a href=\"/jump_to_id/nonportable_link\">link</a>\n\n",
                            "xml_attributes": {"filename": ["html/nonportable_link.xml", "html/nonportable_link.xml"]}
                        }, []),
                    BlockInfo(
                        "badlink", "html", {
                            "data": "<img src=\"/static//file.jpg\" />\n",
                            "xml_attributes" : { "filename" : [  "html/badlink.xml", "html/badlink.xml" ] }
                        }, []),
                    BlockInfo(
                        "with_styling", "html", {
                            "data": "<p style=\"font:italic bold 72px/30px Georgia, serif; color: red; \">Red text here</p>",
                            "xml_attributes": {"filename": ["html/with_styling.xml", "html/with_styling.xml"]}
                        }, []),
                    BlockInfo(
                        "just_img", "html", {
                            "data": "<img src=\"/static/foo_bar.jpg\" />",
                            "xml_attributes": {"filename": [  "html/just_img.xml", "html/just_img.xml" ] }
                        }, []),
                    BlockInfo(
                        "Video_Resources", "video", {
                            "youtube_id_1_0" : "1bK-WdDi6Qw", "display_name" : "Video Resources"
                        }, []),
                ]),
            BlockInfo(
                "Welcome", "video", {"data": "", "youtube_id_1_0": "p2Q6BrNhdh8", "display_name": "Welcome"}, []
            ),
            BlockInfo(
                "video_123456789012", "video", {"data": "", "youtube_id_1_0": "p2Q6BrNhdh8", "display_name": "Test Video"}, []
            ),
            BlockInfo(
                "video_4f66f493ac8f", "video", {"youtube_id_1_0": "p2Q6BrNhdh8"}, []
            )
        ]
    ),
    BlockInfo(
        "secret:magic", "chapter", {
            "xml_attributes": {"filename": [ "chapter/secret/magic.xml", "chapter/secret/magic.xml"]}
        }, [
            BlockInfo(
                "toyvideo", "video", {"youtube_id_1_0": "OEoXaMPEzfMA", "display_name": "toyvideo"}, []
            )
        ]
    ),
    BlockInfo(
       "poll_test", "chapter", {}, [
            BlockInfo(
                "T1_changemind_poll_foo", "poll_question", {
                    "question": "<p>Have you changed your mind? ’</p>",
                    "answers": [{"text": "Yes", "id": "yes"}, {"text": "No", "id": "no"}],
                    "xml_attributes": {"reset": "false", "filename": ["", None]},
                    "display_name": "Change your answer"
                }, []) ]
    ),
    BlockInfo(
       "vertical_container", "chapter", {
           "xml_attributes": {"filename": ["chapter/vertical_container.xml", "chapter/vertical_container.xml"]}
        }, [
            BlockInfo("vertical_sequential", "sequential", {}, [
                BlockInfo("vertical_test", "vertical", {
                    "xml_attributes": {"filename": ["vertical/vertical_test.xml", "vertical_test"]}
                }, [
                    BlockInfo(
                        "sample_video", "video", {
                            "youtube_id_1_25": "AKqURZnYqpk",
                            "youtube_id_0_75": "JMD_ifUUfsU",
                            "youtube_id_1_0": "OEoXaMPEzfM",
                            "display_name": "default",
                            "youtube_id_1_5": "DYpADpL7jAY"
                        }, []),
                    BlockInfo(
                        "separate_file_video", "video", {
                            "youtube_id_1_25": "AKqURZnYqpk",
                            "youtube_id_0_75": "JMD_ifUUfsU",
                            "youtube_id_1_0": "OEoXaMPEzfM",
                            "display_name": "default",
                            "youtube_id_1_5": "DYpADpL7jAY"
                        }, []),
                    BlockInfo(
                        "video_with_end_time", "video", {
                            "youtube_id_1_25": "AKqURZnYqpk",
                            "display_name": "default",
                            "youtube_id_1_0": "OEoXaMPEzfM",
                            "end_time": datetime.timedelta(seconds=10),
                            "youtube_id_1_5": "DYpADpL7jAY",
                            "youtube_id_0_75": "JMD_ifUUfsU"
                        }, []),
                    BlockInfo(
                        "T1_changemind_poll_foo_2", "poll_question", {
                            "question": "<p>Have you changed your mind?</p>",
                            "answers": [{"text": "Yes", "id": "yes"}, {"text": "No", "id": "no"}],
                            "xml_attributes": {"reset": "false", "filename": [  "", None]},
                            "display_name": "Change your answer"
                        }, []),
                ]),
                BlockInfo("unicode", "html", {
                    "data": "…", "xml_attributes": {"filename": ["", None]}
                }, [])
            ]),
        ]
    ),
    BlockInfo(
       "handout_container", "chapter", {
            "xml_attributes" : {"filename" : ["chapter/handout_container.xml", "chapter/handout_container.xml"]}
        }, [
            BlockInfo(
                "html_7e5578f25f79", "html", {
                    "data": "<a href=\"/static/handouts/sample_handout.txt\"> handouts</a>",
                    "xml_attributes": {"filename": ["", None]}
                }, []
            ),
        ]
    )
]

class ModuleStoreTestCase(TestCase):
    """
    Subclass for any test case that uses a ModuleStore.
    Ensures that the ModuleStore is cleaned before/after each test.

    Usage:

        1. Create a subclass of `ModuleStoreTestCase`
        2. Use Django's @override_settings decorator to use
           the desired modulestore configuration.

           For example:

               MIXED_CONFIG = mixed_store_config(data_dir, mappings)

               @override_settings(MODULESTORE=MIXED_CONFIG)
               class FooTest(ModuleStoreTestCase):
                   # ...

        3. Use factories (e.g. `CourseFactory`, `ItemFactory`) to populate
           the modulestore with test data.

    NOTE:
        * For Mongo-backed courses (created with `CourseFactory`),
          the state of the course will be reset before/after each
          test method executes.

        * For XML-backed courses, the course state will NOT
          reset between test methods (although it will reset
          between test classes)

          The reason is: XML courses are not editable, so to reset
          a course you have to reload it from disk, which is slow.

          If you do need to reset an XML course, use
          `clear_existing_modulestores()` directly in
          your `setUp()` method.
    """
    def setUp(self, **kwargs):
        """
        Creates a test User if `create_user` is True.
        Returns the password for the test User.

        Args:
            create_user - specifies whether or not to create a test User.  Default is True.
        """
        super(ModuleStoreTestCase, self).setUp()

        self.store = modulestore()

        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'

        if kwargs.pop('create_user', True):
            # Create the user so we can log them in.
            self.user = User.objects.create_user(uname, email, password)

            # Note that we do not actually need to do anything
            # for registration if we directly mark them active.
            self.user.is_active = True

            # Staff has access to view all courses
            self.user.is_staff = True
            self.user.save()

        return password

    def create_non_staff_user(self):
        """
        Creates a non-staff test user.
        Returns the non-staff test user and its password.
        """
        uname = 'teststudent'
        password = 'foo'
        nonstaff_user = User.objects.create_user(uname, 'test+student@edx.org', password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        nonstaff_user.is_active = True
        nonstaff_user.is_staff = False
        nonstaff_user.save()
        return nonstaff_user, password

    def update_course(self, course, user_id):
        """
        Updates the version of course in the modulestore

        'course' is an instance of CourseDescriptor for which we want
        to update metadata.
        """
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course.id):
            self.store.update_item(course, user_id)
        updated_course = self.store.get_course(course.id)
        return updated_course

    @staticmethod
    def drop_mongo_collections():
        """
        If using a Mongo-backed modulestore & contentstore, drop the collections.
        """
        module_store = modulestore()
        if hasattr(module_store, '_drop_database'):
            module_store._drop_database()  # pylint: disable=protected-access
        _CONTENTSTORE.clear()

    @classmethod
    def setUpClass(cls):
        """
        Delete the existing modulestores, causing them to be reloaded.
        """
        # Clear out any existing modulestores,
        # which will cause them to be re-created
        # the next time they are accessed.
        clear_existing_modulestores()
        TestCase.setUpClass()

    def _pre_setup(self):
        """
        Flush the ModuleStore.
        """

        # Flush the Mongo modulestore
        self.drop_mongo_collections()

        # Call superclass implementation
        super(ModuleStoreTestCase, self)._pre_setup()

    def _post_teardown(self):
        """
        Flush the ModuleStore after each test.
        """
        self.drop_mongo_collections()
        # Clear out the existing modulestores,
        # which will cause them to be re-created
        # the next time they are accessed.
        # We do this at *both* setup and teardown just to be safe.
        clear_existing_modulestores()

        # Call superclass implementation
        super(ModuleStoreTestCase, self)._post_teardown()

    def create_sample_course(self, org, course, run, block_info_tree=default_block_info_tree, course_fields=None):
        """
        create a course in the default modulestore from the collection of BlockInfo
        records defining the course tree
        Returns:
            course_loc: the CourseKey for the created course
        """
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, None):
            # TODO use a single transaction (version, inheritance cache, etc) for this whole thing
            course = self.store.create_course(org, course, run, self.user.id, fields=course_fields)
            self.course_loc = course.location

            def create_sub_tree(parent_loc, block_info):
                block = self.store.create_child(
                    self.user.id,
                    # TODO remove version_agnostic() when we impl the single transaction
                    parent_loc.version_agnostic(),
                    block_info.category, block_id=block_info.block_id,
                    fields=block_info.fields,
                )
                for tree in block_info.sub_tree:
                    create_sub_tree(block.location, tree)
                setattr(self, block_info.block_id, block.location.version_agnostic())

            for tree in block_info_tree:
                create_sub_tree(self.course_loc, tree)

            self.store.publish(self.course_loc, self.user.id)
        return self.course_loc.course_key.version_agnostic()

    def create_toy_course(self, org='edX', course='toy', run='2012_Fall'):
        """
        Create an equiavlent to the toy xml course
        """
        self.toy_loc = self.create_sample_course(
            org, course, run, TOY_BLOCK_INFO_TREE,
            {
                "textbooks" : [["Textbook", "https://s3.amazonaws.com/edx-textbooks/guttag_computation_v3/"]],
                "wiki_slug" : "toy",
                "display_name" : "Toy Course",
                "graded" : True,
                "tabs" : [
                     CoursewareTab(),  # {"type" : "courseware", "name" : "Courseware"},
                     CourseInfoTab(),  # {"type" : "course_info", "name" : "Course Info"},
                     StaticTab(name="Syllabus", url_slug="syllabus"),
                     StaticTab(name="Resources", url_slug="resources"),
                     DiscussionTab(),
                     WikiTab(),
                     ProgressTab(),
                ],
                "discussion_topics" : {"General" : {"id" : "i4x-edX-toy-course-2012_Fall"}},
                "graceperiod" : datetime.timedelta(days=2, seconds=21599),
                "start" : datetime.datetime(2015, 07, 17, 12, tzinfo=pytz.utc),
                "xml_attributes" : {"filename" : ["course/2012_Fall.xml", "course/2012_Fall.xml"]},
                "pdf_textbooks" : [
                    {
                        "tab_title" : "Sample Multi Chapter Textbook",
                        "id" : "MyTextbook",
                        "chapters" : [
                             {"url" : "/static/Chapter1.pdf", "title" : "Chapter 1"},
                             {"url" : "/static/Chapter2.pdf", "title" : "Chapter 2"}
                        ]
                     }
                ],
                "course_image" : "just_a_test.jpg",
            }
        )
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.toy_loc):
            self.store.create_item(
                self.user.id, self.toy_loc, "about", block_id="short_description",
                fields={"data" : "A course about toys."}
            )
            self.store.create_item(
                self.user.id, self.toy_loc, "about", block_id="effort",
                fields={"data": "6 hours"}
            )
            self.store.create_item(
                self.user.id, self.toy_loc, "about", block_id="end_date",
                fields={"data": "TBD"}
            )
            self.store.create_item(
                self.user.id, self.toy_loc, "about", block_id="overview",
                fields={
                    "data": "<section class=\"about\">\n  <h2>About This Course</h2>\n  <p>Include your long course description here. The long course description should contain 150-400 words.</p>\n\n  <p>This is paragraph 2 of the long course description. Add more paragraphs as needed. Make sure to enclose them in paragraph tags.</p>\n</section>\n\n<section class=\"prerequisites\">\n  <h2>Prerequisites</h2>\n  <p>Add information about course prerequisites here.</p>\n</section>\n\n<section class=\"course-staff\">\n  <h2>Course Staff</h2>\n  <article class=\"teacher\">\n    <div class=\"teacher-image\">\n      <img src=\"/static/images/pl-faculty.png\" align=\"left\" style=\"margin:0 20 px 0\" alt=\"Course Staff Image #1\">\n    </div>\n\n    <h3>Staff Member #1</h3>\n    <p>Biography of instructor/staff member #1</p>\n  </article>\n\n  <article class=\"teacher\">\n    <div class=\"teacher-image\">\n      <img src=\"/static/images/pl-faculty.png\" align=\"left\" style=\"margin:0 20 px 0\" alt=\"Course Staff Image #2\">\n    </div>\n\n    <h3>Staff Member #2</h3>\n    <p>Biography of instructor/staff member #2</p>\n  </article>\n</section>\n\n<section class=\"faq\">\n  <section class=\"responses\">\n    <h2>Frequently Asked Questions</h2>\n    <article class=\"response\">\n      <h3>Do I need to buy a textbook?</h3>\n      <p>No, a free online version of Chemistry: Principles, Patterns, and Applications, First Edition by Bruce Averill and Patricia Eldredge will be available, though you can purchase a printed version (published by FlatWorld Knowledge) if you’d like.</p>\n    </article>\n\n    <article class=\"response\">\n      <h3>Question #2</h3>\n      <p>Your answer would be displayed here.</p>\n    </article>\n  </section>\n</section>\n"
                }
            )
            self.store.create_item(
                self.user.id, self.toy_loc, "course_info", "handouts",
                fields={"data": "<a href='/static/handouts/sample_handout.txt'>Sample</a>"}
            )
            self.store.create_item(
                self.user.id, self.toy_loc, "static_tab", "resources",
                fields={"display_name": "Resources"},
            )
            self.store.create_item(
                self.user.id, self.toy_loc, "static_tab", "syllabus",
                fields={"display_name": "Syllabus"},
            )
        return self.toy_loc
