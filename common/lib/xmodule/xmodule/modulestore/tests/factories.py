"""
Factories for use in tests of XBlocks.
"""

import datetime
import functools
import pymongo.message
import pytz
import threading
import traceback
from collections import defaultdict
from contextlib import contextmanager
from uuid import uuid4

from factory import Factory, Sequence, lazy_attribute_sequence, lazy_attribute
from factory.containers import CyclicDefinitionError
from mock import patch
from nose.tools import assert_less_equal, assert_greater_equal
import dogstats_wrapper as dog_stats_api

from opaque_keys.edx.locations import Location
from opaque_keys.edx.keys import UsageKey
from xblock.core import XBlock
from xmodule.modulestore import prefer_xmodules, ModuleStoreEnum
from xmodule.modulestore.tests.sample_courses import default_block_info_tree, TOY_BLOCK_INFO_TREE
from xmodule.tabs import CourseTab
from xmodule.x_module import DEPRECATION_VSCOMPAT_EVENT
from xmodule.course_module import Textbook


class Dummy(object):
    pass


class XModuleFactoryLock(threading.local):
    """
    This class exists to store whether XModuleFactory can be accessed in a safe
    way (meaning, in a context where the data it creates will be cleaned up).

    Users of XModuleFactory (or its subclasses) should only call XModuleFactoryLock.enable
    after ensuring that a) the modulestore will be cleaned up, and b) that XModuleFactoryLock.disable
    will be called.
    """
    def __init__(self):
        super(XModuleFactoryLock, self).__init__()
        self._enabled = False

    def enable(self):
        """
        Enable XModuleFactories. This should only be turned in a context
        where the modulestore will be reset at the end of the test (such
        as inside ModuleStoreTestCase).
        """
        self._enabled = True

    def disable(self):
        """
        Disable XModuleFactories. This should be called once the data
        from the factory has been cleaned up.
        """
        self._enabled = False

    def is_enabled(self):
        """
        Return whether XModuleFactories are enabled.
        """
        return self._enabled


XMODULE_FACTORY_LOCK = XModuleFactoryLock()


class XModuleFactory(Factory):
    """
    Factory for XModules
    """

    # We have to give a model for Factory.
    # However, the class that we create is actually determined by the category
    # specified in the factory
    class Meta(object):
        model = Dummy

    @lazy_attribute
    def modulestore(self):
        msg = "XMODULE_FACTORY_LOCK not enabled. Please use ModuleStoreTestCase as your test baseclass."
        assert XMODULE_FACTORY_LOCK.is_enabled(), msg

        from xmodule.modulestore.django import modulestore
        return modulestore()


last_course = threading.local()


class CourseFactory(XModuleFactory):
    """
    Factory for XModule courses.
    """
    org = Sequence('org.{}'.format)
    number = Sequence('course_{}'.format)
    display_name = Sequence('Run {}'.format)

    # pylint: disable=unused-argument
    @classmethod
    def _create(cls, target_class, **kwargs):
        """
        Create and return a new course. For performance reasons, we do not emit
        signals during this process, but if you need signals to run, you can
        pass `emit_signals=True` to this method.
        """
        # All class attributes (from this class and base classes) are
        # passed in via **kwargs. However, some of those aren't actual field values,
        # so pop those off for use separately
        org = kwargs.pop('org', None)
        # because the factory provides a default 'number' arg, prefer the non-defaulted 'course' arg if any
        number = kwargs.pop('course', kwargs.pop('number', None))
        store = kwargs.pop('modulestore')
        name = kwargs.get('name', kwargs.get('run', Location.clean(kwargs.get('display_name'))))
        run = kwargs.pop('run', name)
        user_id = kwargs.pop('user_id', ModuleStoreEnum.UserID.test)
        emit_signals = kwargs.pop('emit_signals', False)

        # Pass the metadata just as field=value pairs
        kwargs.update(kwargs.pop('metadata', {}))
        default_store_override = kwargs.pop('default_store', None)

        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            course_key = store.make_course_key(org, number, run)
            with store.bulk_operations(course_key, emit_signals=emit_signals):
                if default_store_override is not None:
                    with store.default_store(default_store_override):
                        new_course = store.create_course(org, number, run, user_id, fields=kwargs)
                else:
                    new_course = store.create_course(org, number, run, user_id, fields=kwargs)

                last_course.loc = new_course.location
                return new_course


class SampleCourseFactory(CourseFactory):
    """
    Factory for sample courses using block_info_tree definitions.
    """
    @classmethod
    def _create(cls, target_class, **kwargs):
        """
        Create and return a new sample course. See CourseFactory for customization kwargs.
        """
        block_info_tree = kwargs.pop('block_info_tree', default_block_info_tree)
        store = kwargs.get('modulestore')
        user_id = kwargs.get('user_id', ModuleStoreEnum.UserID.test)
        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, None):
            course = super(SampleCourseFactory, cls)._create(target_class, **kwargs)

            def create_sub_tree(parent_loc, block_info):
                """Recursively creates a sub_tree on this parent_loc with this block."""
                block = store.create_child(
                    user_id,
                    parent_loc,
                    block_info.category,
                    block_id=block_info.block_id,
                    fields=block_info.fields,
                )
                for tree in block_info.sub_tree:
                    create_sub_tree(block.location, tree)

            for tree in block_info_tree:
                create_sub_tree(course.location, tree)

            store.publish(course.location, user_id)
        return course


class ToyCourseFactory(SampleCourseFactory):
    """
    Factory for sample course that is equivalent to the toy xml course.
    """
    org = 'edX'
    course = 'toy'
    run = '2012_Fall'
    display_name = 'Toy Course'

    @classmethod
    def _create(cls, target_class, **kwargs):
        """
        Create and return a new toy course instance. See SampleCourseFactory for customization kwargs.
        """
        store = kwargs.get('modulestore')
        user_id = kwargs.get('user_id', ModuleStoreEnum.UserID.test)

        fields = {
            'block_info_tree': TOY_BLOCK_INFO_TREE,
            'textbooks': [Textbook("Textbook", "path/to/a/text_book")],
            'wiki_slug': "toy",
            'graded': True,
            'discussion_topics': {"General": {"id": "i4x-edX-toy-course-2012_Fall"}},
            'graceperiod': datetime.timedelta(days=2, seconds=21599),
            'start': datetime.datetime(2015, 07, 17, 12, tzinfo=pytz.utc),
            'xml_attributes': {"filename": ["course/2012_Fall.xml", "course/2012_Fall.xml"]},
            'pdf_textbooks': [
                {
                    "tab_title": "Sample Multi Chapter Textbook",
                    "id": "MyTextbook",
                    "chapters": [
                        {"url": "/static/Chapter1.pdf", "title": "Chapter 1"},
                        {"url": "/static/Chapter2.pdf", "title": "Chapter 2"}
                    ]
                }
            ],
            'course_image': "just_a_test.jpg",
        }
        fields.update(kwargs)

        toy_course = super(ToyCourseFactory, cls)._create(
            target_class,
            **fields
        )
        with store.bulk_operations(toy_course.id, emit_signals=False):
            with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, toy_course.id):
                store.create_item(
                    user_id, toy_course.id, "about", block_id="short_description",
                    fields={"data": "A course about toys."}
                )
                store.create_item(
                    user_id, toy_course.id, "about", block_id="effort",
                    fields={"data": "6 hours"}
                )
                store.create_item(
                    user_id, toy_course.id, "about", block_id="end_date",
                    fields={"data": "TBD"}
                )
                store.create_item(
                    user_id, toy_course.id, "course_info", "handouts",
                    fields={"data": "<a href='/static/handouts/sample_handout.txt'>Sample</a>"}
                )
                store.create_item(
                    user_id, toy_course.id, "static_tab", "resources",
                    fields={"display_name": "Resources"},
                )
                store.create_item(
                    user_id, toy_course.id, "static_tab", "syllabus",
                    fields={"display_name": "Syllabus"},
                )
        return toy_course


class LibraryFactory(XModuleFactory):
    """
    Factory for creating a content library
    """
    org = Sequence('org{}'.format)
    library = Sequence('lib{}'.format)
    display_name = Sequence('Test Library {}'.format)

    # pylint: disable=unused-argument
    @classmethod
    def _create(cls, target_class, **kwargs):
        """
        Create a library with a unique name and key.
        All class attributes (from this class and base classes) are automagically
        passed in via **kwargs.
        """
        # some of the kwargst actual field values, so pop those off for use separately:
        org = kwargs.pop('org')
        library = kwargs.pop('library')
        store = kwargs.pop('modulestore')
        user_id = kwargs.pop('user_id', ModuleStoreEnum.UserID.test)

        # Pass the metadata just as field=value pairs
        kwargs.update(kwargs.pop('metadata', {}))
        default_store_override = kwargs.pop('default_store', ModuleStoreEnum.Type.split)
        with store.default_store(default_store_override):
            new_library = store.create_library(org, library, user_id, fields=kwargs)
            return new_library


class ItemFactory(XModuleFactory):
    """
    Factory for XModule items.
    """

    category = 'chapter'
    parent = None

    @lazy_attribute_sequence
    def display_name(self, n):
        return "{} {}".format(self.category, n)

    @lazy_attribute
    def location(self):
        if self.display_name is None:
            dest_name = uuid4().hex
        else:
            dest_name = self.display_name.replace(" ", "_")

        new_location = self.parent_location.course_key.make_usage_key(
            self.category,
            dest_name
        )
        return new_location

    @lazy_attribute
    def parent_location(self):
        default_location = getattr(last_course, 'loc', None)
        try:
            parent = self.parent
        # This error is raised if the caller hasn't provided either parent or parent_location
        # In this case, we'll just return the default parent_location
        except CyclicDefinitionError:
            return default_location

        if parent is None:
            return default_location

        return parent.location

    @classmethod
    def _create(cls, target_class, **kwargs):
        """
        Uses ``**kwargs``:

        :parent_location: (required): the location of the parent module
            (e.g. the parent course or section)

        :category: the category of the resulting item.

        :data: (optional): the data for the item
            (e.g. XML problem definition for a problem item)

        :display_name: (optional): the display name of the item

        :metadata: (optional): dictionary of metadata attributes

        :boilerplate: (optional) the boilerplate for overriding field values

        :publish_item: (optional) whether or not to publish the item (default is True)

        :target_class: is ignored
        """

        # All class attributes (from this class and base classes) are
        # passed in via **kwargs. However, some of those aren't actual field values,
        # so pop those off for use separately

        # catch any old style users before they get into trouble
        assert 'template' not in kwargs
        parent_location = kwargs.pop('parent_location', None)
        data = kwargs.pop('data', None)
        category = kwargs.pop('category', None)
        display_name = kwargs.pop('display_name', None)
        metadata = kwargs.pop('metadata', {})
        location = kwargs.pop('location')
        user_id = kwargs.pop('user_id', ModuleStoreEnum.UserID.test)
        publish_item = kwargs.pop('publish_item', True)

        assert isinstance(location, UsageKey)
        assert location != parent_location

        store = kwargs.pop('modulestore')

        # This code was based off that in cms/djangoapps/contentstore/views.py
        parent = kwargs.pop('parent', None) or store.get_item(parent_location)

        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):

            if 'boilerplate' in kwargs:
                template_id = kwargs.pop('boilerplate')
                clz = XBlock.load_class(category, select=prefer_xmodules)
                template = clz.get_template(template_id)
                assert template is not None
                metadata.update(template.get('metadata', {}))
                if not isinstance(data, basestring):
                    data.update(template.get('data'))

            # replace the display name with an optional parameter passed in from the caller
            if display_name is not None:
                metadata['display_name'] = display_name

            module = store.create_child(
                user_id,
                parent.location,
                location.block_type,
                block_id=location.block_id,
                metadata=metadata,
                definition_data=data,
                runtime=parent.runtime,
                fields=kwargs,
            )

            # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
            # if we add one then we need to also add it to the policy information (i.e. metadata)
            # we should remove this once we can break this reference from the course to static tabs
            if category == 'static_tab':
                dog_stats_api.increment(
                    DEPRECATION_VSCOMPAT_EVENT,
                    tags=(
                        "location:itemfactory_create_static_tab",
                        u"block:{}".format(location.block_type),
                    )
                )

                course = store.get_course(location.course_key)
                course.tabs.append(
                    CourseTab.load('static_tab', name='Static Tab', url_slug=location.name)
                )
                store.update_item(course, user_id)

            # parent and publish the item, so it can be accessed
            if 'detached' not in module._class_tags:
                parent.children.append(location)
                store.update_item(parent, user_id)
                if publish_item:
                    published_parent = store.publish(parent.location, user_id)
                    # module is last child of parent
                    return published_parent.get_children()[-1]
                else:
                    return store.get_item(location)
            elif publish_item:
                return store.publish(location, user_id)
            else:
                return module


@contextmanager
def check_exact_number_of_calls(object_with_method, method_name, num_calls):
    """
    Instruments the given method on the given object to verify the number of calls to the
    method is exactly equal to 'num_calls'.
    """
    with check_number_of_calls(object_with_method, method_name, num_calls, num_calls):
        yield


def check_number_of_calls(object_with_method, method_name, maximum_calls, minimum_calls=1):
    """
    Instruments the given method on the given object to verify the number of calls to the method is
    less than or equal to the expected maximum_calls and greater than or equal to the expected minimum_calls.
    """
    return check_sum_of_calls(object_with_method, [method_name], maximum_calls, minimum_calls)


class StackTraceCounter(object):
    """
    A class that counts unique stack traces underneath a particular stack frame.
    """
    def __init__(self, stack_depth, include_arguments=True):
        """
        Arguments:
            stack_depth (int): The number of stack frames above this constructor to capture.
            include_arguments (bool): Whether to store the arguments that are passed
                when capturing a stack trace.
        """
        self.include_arguments = include_arguments
        self._top_of_stack = traceback.extract_stack(limit=stack_depth)[0]

        if self.include_arguments:
            self._stacks = defaultdict(lambda: defaultdict(int))
        else:
            self._stacks = defaultdict(int)

    def capture_stack(self, args, kwargs):
        """
        Record the stack frames starting at the caller of this method, and
        ending at the top of the stack as defined by the ``stack_depth``.

        Arguments:
            args: The positional arguments to capture at this stack frame
            kwargs: The keyword arguments to capture at this stack frame
        """
        # pylint: disable=broad-except

        stack = traceback.extract_stack()[:-2]

        if self._top_of_stack in stack:
            stack = stack[stack.index(self._top_of_stack):]

        if self.include_arguments:
            safe_args = []
            for arg in args:
                try:
                    safe_args.append(repr(arg))
                except Exception as exc:
                    safe_args.append('<un-repr-able value: {}'.format(exc))

            safe_kwargs = {}
            for key, kwarg in kwargs.items():
                try:
                    safe_kwargs[key] = repr(kwarg)
                except Exception as exc:
                    safe_kwargs[key] = '<un-repr-able value: {}'.format(exc)

            self._stacks[tuple(stack)][tuple(safe_args), tuple(safe_kwargs.items())] += 1
        else:
            self._stacks[tuple(stack)] += 1

    @property
    def total_calls(self):
        """
        Return the total number of stacks recorded.
        """
        return sum(self.stack_calls(stack) for stack in self._stacks)

    def stack_calls(self, stack):
        """
        Return the number of calls to the supplied ``stack``.
        """
        if self.include_arguments:
            return sum(self._stacks[stack].values())
        else:
            return self._stacks[stack]

    def __iter__(self):
        """
        Iterate over all unique captured stacks.
        """
        return iter(sorted(self._stacks.keys(), key=lambda stack: (self.stack_calls(stack), stack), reverse=True))

    def __getitem__(self, stack):
        """
        Return the set of captured calls with the supplied stack.
        """
        return self._stacks[stack]

    @classmethod
    def capture_call(cls, func, stack_depth, include_arguments=True):
        """
        A decorator that wraps ``func``, and captures each call to ``func``,
        recording the stack trace, and optionally the arguments that the function
        is called with.

        Arguments:
            func: the function to wrap
            stack_depth: how far up the stack to truncate the stored stack traces (
                this is counted from the call to ``capture_call``, rather than calls
                to the captured function).

        """
        stacks = StackTraceCounter(stack_depth, include_arguments)

        # pylint: disable=missing-docstring
        @functools.wraps(func)
        def capture(*args, **kwargs):
            stacks.capture_stack(args, kwargs)
            return func(*args, **kwargs)

        capture.stack_counter = stacks

        return capture


@contextmanager
def check_sum_of_calls(object_, methods, maximum_calls, minimum_calls=1, include_arguments=True):
    """
    Instruments the given methods on the given object to verify that the total sum of calls made to the
    methods falls between minumum_calls and maximum_calls.
    """

    mocks = {
        method: StackTraceCounter.capture_call(
            getattr(object_, method),
            stack_depth=7,
            include_arguments=include_arguments
        )
        for method in methods
    }

    with patch.multiple(object_, **mocks):
        yield

    call_count = sum(capture_fn.stack_counter.total_calls for capture_fn in mocks.values())

    # Assertion errors don't handle multi-line values, so pretty-print to std-out instead
    if not minimum_calls <= call_count <= maximum_calls:
        messages = ["Expected between {} and {} calls, {} were made.\n\n".format(
            minimum_calls,
            maximum_calls,
            call_count,
        )]
        for method_name, capture_fn in mocks.items():
            stack_counter = capture_fn.stack_counter
            messages.append("{!r} was called {} times:\n".format(
                method_name,
                stack_counter.total_calls
            ))
            for stack in stack_counter:
                messages.append("  called {} times:\n\n".format(stack_counter.stack_calls(stack)))
                messages.append("    " + "    ".join(traceback.format_list(stack)))
                messages.append("\n\n")
                if include_arguments:
                    for (args, kwargs), count in stack_counter[stack].items():
                        messages.append("      called {} times with:\n".format(count))
                        messages.append("      args: {}\n".format(args))
                        messages.append("      kwargs: {}\n\n".format(dict(kwargs)))

        print "".join(messages)

    # verify the counter actually worked by ensuring we have counted greater than (or equal to) the minimum calls
    assert_greater_equal(call_count, minimum_calls)

    # now verify the number of actual calls is less than (or equal to) the expected maximum
    assert_less_equal(call_count, maximum_calls)


def mongo_uses_error_check(store):
    """
    Does mongo use the error check as a separate message?
    """
    if hasattr(store, 'mongo_wire_version'):
        return store.mongo_wire_version() <= 1
    if hasattr(store, 'modulestores'):
        return any([mongo_uses_error_check(substore) for substore in store.modulestores])
    return False


@contextmanager
def check_mongo_calls_range(max_finds=float("inf"), min_finds=0, max_sends=None, min_sends=None):
    """
    Instruments the given store to count the number of calls to find (incl find_one) and the number
    of calls to send_message which is for insert, update, and remove (if you provide num_sends). At the
    end of the with statement, it compares the counts to the bounds provided in the arguments.

    :param max_finds: the maximum number of find calls expected
    :param min_finds: the minimum number of find calls expected
    :param max_sends: If non-none, make sure number of send calls are <=max_sends
    :param min_sends: If non-none, make sure number of send calls are >=min_sends
    """
    with check_sum_of_calls(
        pymongo.message,
        ['query', 'get_more'],
        max_finds,
        min_finds,
    ):
        if max_sends is not None or min_sends is not None:
            with check_sum_of_calls(
                pymongo.message,
                # mongo < 2.6 uses insert, update, delete and _do_batched_insert. >= 2.6 _do_batched_write
                ['insert', 'update', 'delete', '_do_batched_write_command', '_do_batched_insert', ],
                max_sends if max_sends is not None else float("inf"),
                min_sends if min_sends is not None else 0,
            ):
                yield
        else:
            yield


@contextmanager
def check_mongo_calls(num_finds=0, num_sends=None):
    """
    Instruments the given store to count the number of calls to find (incl find_one) and the number
    of calls to send_message which is for insert, update, and remove (if you provide num_sends). At the
    end of the with statement, it compares the counts to the num_finds and num_sends.

    :param num_finds: the exact number of find calls expected
    :param num_sends: If none, don't instrument the send calls. If non-none, count and compare to
        the given int value.
    """
    with check_mongo_calls_range(num_finds, num_finds, num_sends, num_sends):
        yield

# This dict represents the attribute keys for a course's 'about' info.
# Note: The 'video' attribute is intentionally excluded as it must be
# handled separately; its value maps to an alternate key name.
# Reference : from openedx.core.djangoapps.models.course_details.py


ABOUT_ATTRIBUTES = {
    'effort': "Testing effort",
}


class CourseAboutFactory(XModuleFactory):
    """
    Factory for XModule course about.
    """

    @classmethod
    def _create(cls, target_class, **kwargs):  # pylint: disable=unused-argument
        """
        Uses **kwargs:

        effort:  effor information

        video : video link
        """
        user_id = kwargs.pop('user_id', None)
        course_id, course_runtime = kwargs.pop("course_id"), kwargs.pop("course_runtime")
        store = kwargs.pop('modulestore')
        for about_key in ABOUT_ATTRIBUTES:
            about_item = store.create_xblock(course_runtime, course_id, 'about', about_key)
            about_item.data = ABOUT_ATTRIBUTES[about_key]
            store.update_item(about_item, user_id, allow_not_found=True)
        about_item = store.create_xblock(course_runtime, course_id, 'about', 'video')
        about_item.data = "www.youtube.com/embed/testing-video-link"
        store.update_item(about_item, user_id, allow_not_found=True)
