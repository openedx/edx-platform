u"""
Testing persistent tasks
"""

from __future__ import print_function

from celery import task
from django.test import TestCase
import six

from openedx.core.djangolib.testing.utils import skip_unless_lms
from ..models import FailedTask
from ..task import PersistOnFailureTask


@skip_unless_lms
class PersistOnFailureTaskTestCase(TestCase):
    """
    Test that persistent tasks save the appropriate values when needed.
    """

    @classmethod
    def setUpClass(cls):
        @task(base=PersistOnFailureTask)
        def exampletask(message=None):
            u"""
            A simple task for testing persistence
            """
            if message:
                raise ValueError(message)
            return
        cls.exampletask = exampletask
        super(PersistOnFailureTaskTestCase, cls).setUpClass()

    def test_exampletask_without_failure(self):
        result = self.exampletask.delay()
        result.wait()
        self.assertEqual(result.status, u'SUCCESS')
        self.assertFalse(FailedTask.objects.exists())

    def test_exampletask_with_failure(self):
        result = self.exampletask.delay(message=u'The example task failed')
        with self.assertRaises(ValueError):
            result.wait()
        self.assertEqual(result.status, u'FAILURE')
        failed_task_object = FailedTask.objects.get()
        # Assert that we get the kind of data we expect
        self.assertEqual(
            failed_task_object.task_name,
            u'openedx.core.djangoapps.celery_utils.tests.test_task.exampletask'
        )
        self.assertEqual(failed_task_object.args, [])
        self.assertEqual(failed_task_object.kwargs, {u'message': u'The example task failed'})
        self.assertEqual(failed_task_object.exc, u"ValueError(u'The example task failed',)")
        self.assertIsNone(failed_task_object.datetime_resolved)

    def test_persists_when_called_with_wrong_args(self):
        result = self.exampletask.delay(15, u'2001-03-04', err=True)
        with self.assertRaises(TypeError):
            result.wait()
        self.assertEqual(result.status, u'FAILURE')
        failed_task_object = FailedTask.objects.get()
        self.assertEqual(failed_task_object.args, [15, u'2001-03-04'])
        self.assertEqual(failed_task_object.kwargs, {u'err': True})

    def test_persists_with_overlength_field(self):
        overlong_message = u''.join(u'%03d' % x for x in six.moves.range(100))
        result = self.exampletask.delay(message=overlong_message)
        with self.assertRaises(ValueError):
            result.wait()
        failed_task_object = FailedTask.objects.get()
        # Length is max field length
        self.assertEqual(len(failed_task_object.exc), 255)
        # Ellipses are put in the middle
        self.assertEqual(u'037...590', failed_task_object.exc[124:133])
        # The beginning of the input is captured
        self.assertEqual(failed_task_object.exc[:11], u"ValueError(")
        # The end of the input is captured
        self.assertEqual(failed_task_object.exc[-9:], u"098099',)")
