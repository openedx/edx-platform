"""
Test models, managers, and validators.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import ddt

from django.core.exceptions import ValidationError
from django.test import TestCase
from opaque_keys.edx.keys import UsageKey

from student.tests.factories import UserFactory

from .. import models
from .. import waffle


class PercentValidatorTestCase(TestCase):
    """
    Test that validate_percent only allows floats (and ints) between 0.0 and 1.0.
    """
    def test_valid_percents(self):
        for value in [1.0, 0.0, 1, 0, 0.5, 0.333081348071397813987230871]:
            models.validate_percent(value)

    def test_invalid_percent(self):
        for value in [-0.00000000001, 1.0000000001, 47.1, 1000, None, float('inf'), float('nan')]:
            self.assertRaises(ValidationError, models.validate_percent, value)


class CompletionSetUpMixin(object):
    def set_up_completion(self):
        self.user = UserFactory()
        self.block_key = UsageKey.from_string(u'block-v1:edx+test+run+type@video+block@doggos')
        self.completion = models.BlockCompletion.objects.create(
            user=self.user,
            course_key=self.block_key.course_key,
            block_type=self.block_key.block_type,
            block_key=self.block_key,
            completion=0.5,
        )


class SubmitCompletionTestCase(CompletionSetUpMixin, TestCase):
    """
    Test that BlockCompletion.objects.submit_completion has the desired
    semantics.
    """
    def setUp(self):
        super(SubmitCompletionTestCase, self).setUp()
        _overrider = waffle.waffle().override(waffle.ENABLE_COMPLETION_TRACKING, True)
        _overrider.__enter__()
        self.addCleanup(_overrider.__exit__, None, None, None)
        self.set_up_completion()

    def test_changed_value(self):
        with self.assertNumQueries(4):  # Get, update, 2 * savepoints
            completion, isnew = models.BlockCompletion.objects.submit_completion(
                user=self.user,
                course_key=self.block_key.course_key,
                block_key=self.block_key,
                completion=0.9,
            )
        completion.refresh_from_db()
        self.assertEqual(completion.completion, 0.9)
        self.assertFalse(isnew)
        self.assertEqual(models.BlockCompletion.objects.count(), 1)

    def test_unchanged_value(self):
        with self.assertNumQueries(1):  # Get
            completion, isnew = models.BlockCompletion.objects.submit_completion(
                user=self.user,
                course_key=self.block_key.course_key,
                block_key=self.block_key,
                completion=0.5,
            )
        completion.refresh_from_db()
        self.assertEqual(completion.completion, 0.5)
        self.assertFalse(isnew)
        self.assertEqual(models.BlockCompletion.objects.count(), 1)

    def test_new_user(self):
        newuser = UserFactory()
        with self.assertNumQueries(4):  # Get, update, 2 * savepoints
            _, isnew = models.BlockCompletion.objects.submit_completion(
                user=newuser,
                course_key=self.block_key.course_key,
                block_key=self.block_key,
                completion=0.0,
            )
        self.assertTrue(isnew)
        self.assertEqual(models.BlockCompletion.objects.count(), 2)

    def test_new_block(self):
        newblock = UsageKey.from_string(u'block-v1:edx+test+run+type@video+block@puppers')
        with self.assertNumQueries(4):  # Get, update, 2 * savepoints
            _, isnew = models.BlockCompletion.objects.submit_completion(
                user=self.user,
                course_key=newblock.course_key,
                block_key=newblock,
                completion=1.0,
            )
        self.assertTrue(isnew)
        self.assertEqual(models.BlockCompletion.objects.count(), 2)

    def test_invalid_completion(self):
        with self.assertRaises(ValidationError):
            models.BlockCompletion.objects.submit_completion(
                user=self.user,
                course_key=self.block_key.course_key,
                block_key=self.block_key,
                completion=1.2
            )
        completion = models.BlockCompletion.objects.get(user=self.user, block_key=self.block_key)
        self.assertEqual(completion.completion, 0.5)
        self.assertEqual(models.BlockCompletion.objects.count(), 1)


class CompletionDisabledTestCase(CompletionSetUpMixin, TestCase):

    @classmethod
    def setUpClass(cls):
        super(CompletionDisabledTestCase, cls).setUpClass()
        cls.overrider = waffle.waffle().override(waffle.ENABLE_COMPLETION_TRACKING, False)
        cls.overrider.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.overrider.__exit__(None, None, None)
        super(CompletionDisabledTestCase, cls).tearDownClass()

    def setUp(self):
        super(CompletionDisabledTestCase, self).setUp()
        self.set_up_completion()

    def test_cannot_call_submit_completion(self):
        self.assertEqual(models.BlockCompletion.objects.count(), 1)
        with self.assertRaises(RuntimeError):
            models.BlockCompletion.objects.submit_completion(
                user=self.user,
                course_key=self.block_key.course_key,
                block_key=self.block_key,
                completion=0.9,
            )
        self.assertEqual(models.BlockCompletion.objects.count(), 1)


@ddt.ddt
class AggregateCompletionTestCase(TestCase):
    BLOCK_KEY = u'block-v1:edx+test+run+type@video+block@doggos'
    BLOCK_KEY_OBJ = UsageKey.from_string(BLOCK_KEY)
    COURSE_KEY_OBJ = UsageKey.from_string(BLOCK_KEY).course_key

    def setUp(self):
        super(AggregateCompletionTestCase, self).setUp()
        self.user = UserFactory()

        # Enable completion tracking
        overrider = waffle.waffle().override(waffle.ENABLE_COMPLETION_AGGREGATION, True)
        overrider.__enter__()
        self.addCleanup(overrider.__exit__, None, None, None)

    @ddt.data(
        # Valid arguments
        (BLOCK_KEY_OBJ, 'course', 0.5, 1, 0.5),
    )
    @ddt.unpack
    def test_submit_completion_with_valid_data(self, block_key_obj, aggregate_name, earned, possible, expected_percent):
        obj, is_new = models.AggregateCompletion.objects.submit_completion(
            user=self.user,
            course_key=block_key_obj.course_key,
            block_key=block_key_obj,
            aggregation_name=aggregate_name,
            earned=earned,
            possible=possible
        )
        self.assertTrue(is_new)
        self.assertEqual(len(models.AggregateCompletion.objects.all()), 1)
        self.assertEqual(obj.earned, earned)
        self.assertEqual(obj.possible, possible)
        self.assertEqual(obj.percent, expected_percent)

    @ddt.data(
        # Earned greater than possible
        (BLOCK_KEY_OBJ, COURSE_KEY_OBJ, 'course', 1.1, 1,
         ValueError, "The earned cannot be larger than the possible value."),
        # Earned is less than zero.
        (BLOCK_KEY_OBJ, COURSE_KEY_OBJ, 'course', -0.5, 1,
         ValidationError, "{'percent': [u'-0.5 must be between 0.0 and 1.0'],"
                          " 'earned': [u'-0.5 must be larger than 0.']}"),
        # Possible is less than zero.
        (BLOCK_KEY_OBJ, COURSE_KEY_OBJ, 'course', -1.5, -1,
         ValidationError, "{'percent': [u'1.5 must be between 0.0 and 1.0'],"
                          " 'possible': [u'-1.0 must be larger than 0.'],"
                          " 'earned': [u'-1.5 must be larger than 0.']}"),
        # TypeError for Block Key
        (BLOCK_KEY, COURSE_KEY_OBJ, 'course', 0.5, 1,
         TypeError, "{'percent': [u'1.5 must be between 0.0 and 1.0'],"
                    " 'possible': [u'-1.0 must be larger than 0.'],"
                    " 'earned': [u'-1.5 must be larger than 0.']}"),
        # TypeError for Course Key
        (BLOCK_KEY_OBJ, str(COURSE_KEY_OBJ), 'course', 0.5, 1,
         TypeError, "{'percent': [u'1.5 must be between 0.0 and 1.0'],"
                    " 'possible': [u'-1.0 must be larger than 0.'],"
                    " 'earned': [u'-1.5 must be larger than 0.']}"),
    )
    @ddt.unpack
    def test_submit_completion_with_exception(self, block_key, course_key, aggregate_name,
                                              earned, possible, exception_type, exception_message):
        with self.assertRaises(exception_type) as context_manager:
            models.AggregateCompletion.objects.submit_completion(
                user=self.user,
                course_key=course_key,
                block_key=block_key,
                aggregation_name=aggregate_name,
                earned=earned,
                possible=possible)

            self.assertEqual(exception_message, str(context_manager.exception))

    @ddt.data(
        (
            BLOCK_KEY_OBJ, 'course', 0.5, 1, 0.5,
        )
    )
    @ddt.unpack
    def test_aggregate_completion_string(self, block_key_obj, aggregate_name,
                                         earned, possible, expected_percent):
        obj, is_new = models.AggregateCompletion.objects.submit_completion(
            user=self.user,
            course_key=block_key_obj.course_key,
            block_key=block_key_obj,
            aggregation_name=aggregate_name,
            earned=earned,
            possible=possible
        )
        expected_string = 'AggregationCompletion: {username}, course-v1:edx+test+run, ' \
                          'block-v1:edx+test+run+type@video+block@doggos: 0.5'.format(username=self.user.username)
        self.assertEqual(str(obj), expected_string)

    @ddt.data(
        # Changes the value of earned. This does not create a new object.
        (
            BLOCK_KEY_OBJ, 'course', 0.5, 1, 0.5,
            BLOCK_KEY_OBJ, 'course', 0.7, 1, 0.7, False
        ),
        # Changes the value of possible. This does not create a new object.
        (
            BLOCK_KEY_OBJ, 'course', 0.5, 1, 0.5,
            BLOCK_KEY_OBJ, 'course', 0.5, 2, 0.25, False
        ),
        # Changes the value of aggregate_name. This creates a new object.
        (
            BLOCK_KEY_OBJ, 'course', 0.5, 1, 0.5,
            BLOCK_KEY_OBJ, 'chapter', 0.5, 1, 0.5, True
        ),
        # Changes the block_key. This creates a new object.
        (
            BLOCK_KEY_OBJ, 'course', 0.5, 1, 0.5,
            UsageKey.from_string(u'block-v1:edX+DemoX+Demo_Course+type@sequential+block@workflow'),
            'course', 0.5, 1, 0.5, True
        ),
    )
    @ddt.unpack
    def test_submit_completion_twice_with_changes(self, block_key_obj, aggregate_name, earned, possible,
                                                  expected_percent, new_block_key_obj, new_aggregate_name, new_earned,
                                                  new_possible, new_percent, is_second_obj_new):
        obj, is_new = models.AggregateCompletion.objects.submit_completion(
            user=self.user,
            course_key=block_key_obj.course_key,
            block_key=block_key_obj,
            aggregation_name=aggregate_name,
            earned=earned,
            possible=possible
        )
        self.assertEqual(obj.percent, expected_percent)
        self.assertTrue(is_new)

        new_obj, is_new = models.AggregateCompletion.objects.submit_completion(
            user=self.user,
            course_key=new_block_key_obj.course_key,
            block_key=new_block_key_obj,
            aggregation_name=new_aggregate_name,
            earned=new_earned,
            possible=new_possible
        )
        self.assertEqual(new_obj.percent, new_percent)
        self.assertEqual(is_new, is_second_obj_new)
        if is_second_obj_new:
            self.assertNotEqual(obj.id, new_obj.id)


@ddt.ddt
class AggregateCompletionDisabledTestCase(TestCase):

    def setUp(self):
        super(AggregateCompletionDisabledTestCase, self).setUp()
        # Disable completion tracking
        overrider = waffle.waffle().override(waffle.ENABLE_COMPLETION_AGGREGATION, False)
        overrider.__enter__()
        self.addCleanup(overrider.__exit__, None, None, None)

    @ddt.data(
        (RuntimeError, "AggregateCompletion.submit_completion should not be "
                       "called when the aggregation feature is disabled.")
    )
    @ddt.unpack
    def test_cannot_call_submit_completion(self, exception_type, exception_message):
        self.assertEqual(models.AggregateCompletion.objects.count(), 0)
        with self.assertRaises(exception_type) as context_manager:
            models.AggregateCompletion.objects.submit_completion(
                user=None,
                course_key=None,
                block_key=None,
                aggregation_name='course',
                earned=0.5,
                possible=1.0,
            )
            self.assertEqual(exception_message, str(context_manager.exception))
        self.assertEqual(models.AggregateCompletion.objects.count(), 0)
