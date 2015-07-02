"""
Test cases for Call Stack Manager
"""
from mock import patch
from django.db import models
from django.test import TestCase

from openedx.core.djangoapps.call_stack_manager import donottrack, CallStackManager, CallStackMixin


class ModelMixinCallStckMngr(CallStackMixin, models.Model):
    """
    Test Model class which uses both CallStackManager, and CallStackMixin
    """
    # override Manager objects
    objects = CallStackManager()
    id_field = models.IntegerField()


class ModelMixin(CallStackMixin, models.Model):
    """
    Test Model that uses CallStackMixin but does not use CallStackManager
    """
    id_field = models.IntegerField()


class ModelNothingCallStckMngr(models.Model):
    """
    Test Model class that neither uses CallStackMixin nor CallStackManager
    """
    id_field = models.IntegerField()


class ModelAnotherCallStckMngr(models.Model):
    """
    Test Model class that only uses overridden Manager CallStackManager
    """
    objects = CallStackManager()
    id_field = models.IntegerField()


class ModelWithCallStackMngr(models.Model):
    """
    Test Model Class with overridden CallStackManager
    """
    objects = CallStackManager()
    id_field = models.IntegerField()


class ModelWithCallStckMngrChild(ModelWithCallStackMngr):
    """child class of ModelWithCallStackMngr
    """
    objects = CallStackManager()
    child_id_field = models.IntegerField()


@donottrack(ModelWithCallStackMngr)
def donottrack_subclass():
    """ function in which subclass and superclass calls QuerySetAPI
    """
    ModelWithCallStackMngr.objects.filter(id_field=1)
    ModelWithCallStckMngrChild.objects.filter(child_id_field=1)


def track_without_donottrack():
    """ function calling QuerySetAPI, another function, again QuerySetAPI
    """
    ModelAnotherCallStckMngr.objects.filter(id_field=1)
    donottrack_child_func()
    ModelAnotherCallStckMngr.objects.filter(id_field=1)


@donottrack(ModelAnotherCallStckMngr)
def donottrack_child_func():
    """ decorated child function
    """
    # should not be tracked
    ModelAnotherCallStckMngr.objects.filter(id_field=1)

    # should be tracked
    ModelMixinCallStckMngr.objects.filter(id_field=1)


@donottrack(ModelMixinCallStckMngr)
def donottrack_parent_func():
    """ decorated parent function
    """
    # should not  be tracked
    ModelMixinCallStckMngr.objects.filter(id_field=1)
    # should be tracked
    ModelAnotherCallStckMngr.objects.filter(id_field=1)
    donottrack_child_func()


@donottrack()
def donottrack_func_parent():
    """ non-parameterized @donottrack decorated function calling child function
    """
    ModelMixin.objects.all()
    donottrack_func_child()
    ModelMixin.objects.filter(id_field=1)


@donottrack()
def donottrack_func_child():
    """ child decorated non-parameterized function
    """
    # Should not be tracked
    ModelMixin.objects.all()


@patch('openedx.core.djangoapps.call_stack_manager.core.log.info')
@patch('openedx.core.djangoapps.call_stack_manager.core.REGULAR_EXPS', [])
class TestingCallStackManager(TestCase):
    """Tests for call_stack_manager
    1. Tests CallStackManager QuerySetAPI functionality
    2. Tests @donottrack decorator
    """
    def test_save(self, log_capt):
        """ tests save() of CallStackMixin/ applies same for delete()
        classes with CallStackMixin should participate in logging.
        """
        ModelMixin(id_field=1).save()
        self.assertEqual(ModelMixin, log_capt.call_args[0][1])

    def test_withoutmixin_save(self, log_capt):
        """tests save() of CallStackMixin/ applies same for delete()
        classes without CallStackMixin should not participate in logging
        """
        ModelAnotherCallStckMngr(id_field=1).save()
        self.assertEqual(len(log_capt.call_args_list), 0)

    def test_queryset(self, log_capt):
        """ Tests for Overriding QuerySet API
        classes with CallStackManager should get logged.
        """
        ModelAnotherCallStckMngr(id_field=1).save()
        ModelAnotherCallStckMngr.objects.all()
        self.assertEqual(ModelAnotherCallStckMngr, log_capt.call_args[0][1])

    def test_withoutqueryset(self, log_capt):
        """ Tests for Overriding QuerySet API
        classes without CallStackManager should not get logged
        """
        # create and save objects of class not overriding queryset API
        ModelNothingCallStckMngr(id_field=1).save()
        # class not using Manager, should not get logged
        ModelNothingCallStckMngr.objects.all()
        self.assertEqual(len(log_capt.call_args_list), 0)

    def test_donottrack(self, log_capt):
        """ Test for @donottrack
        calls in decorated function should not get logged
        """
        donottrack_func_parent()
        self.assertEqual(len(log_capt.call_args_list), 0)

    def test_parameterized_donottrack(self, log_capt):
        """ Test for parameterized @donottrack
        classes specified in the decorator @donottrack should not get logged
        """
        ModelAnotherCallStckMngr(id_field=1).save()
        ModelMixinCallStckMngr(id_field=1).save()
        donottrack_child_func()
        self.assertEqual(ModelMixinCallStckMngr, log_capt.call_args[0][1])

    def test_nested_parameterized_donottrack(self, log_capt):
        """ Tests parameterized nested @donottrack
        should not track call of classes specified in decorated with scope bounded to the respective class
        """
        ModelAnotherCallStckMngr(id_field=1).save()
        donottrack_parent_func()
        self.assertEqual(ModelAnotherCallStckMngr, log_capt.call_args_list[0][0][1])
        self.assertEqual(ModelMixinCallStckMngr, log_capt.call_args_list[1][0][1])

    def test_nested_parameterized_donottrack_after(self, log_capt):
        """ Tests parameterized nested @donottrack
        QuerySetAPI calls after calling function with @donottrack should get logged
        """
        donottrack_child_func()
        # class with CallStackManager as Manager
        ModelAnotherCallStckMngr(id_field=1).save()
        # test is this- that this should get called.
        ModelAnotherCallStckMngr.objects.filter(id_field=1)
        self.assertEqual(ModelMixinCallStckMngr, log_capt.call_args_list[0][0][1])
        self.assertEqual(ModelAnotherCallStckMngr, log_capt.call_args_list[1][0][1])

    def test_donottrack_called_in_func(self, log_capt):
        """ test for function which calls decorated function
        functions without @donottrack decorator should log
        """
        ModelAnotherCallStckMngr(id_field=1).save()
        ModelMixinCallStckMngr(id_field=1).save()
        track_without_donottrack()
        self.assertEqual(ModelMixinCallStckMngr, log_capt.call_args_list[0][0][1])
        self.assertEqual(ModelAnotherCallStckMngr, log_capt.call_args_list[1][0][1])
        self.assertEqual(ModelMixinCallStckMngr, log_capt.call_args_list[2][0][1])
        self.assertEqual(ModelAnotherCallStckMngr, log_capt.call_args_list[3][0][1])

    def test_donottrack_child_too(self, log_capt):
        """ Test for inheritance
        subclass should not be tracked when superclass is called in a @donottrack decorated function
        """
        ModelWithCallStackMngr(id_field=1).save()
        ModelWithCallStckMngrChild(id_field=1, child_id_field=1).save()
        donottrack_subclass()
        self.assertEqual(len(log_capt.call_args_list), 0)

    def test_duplication(self, log_capt):
        """ Test for duplication of call stacks
        should not log duplicated call stacks
        """
        for __ in range(1, 5):
            ModelMixinCallStckMngr(id_field=1).save()
        self.assertEqual(len(log_capt.call_args_list), 1)
