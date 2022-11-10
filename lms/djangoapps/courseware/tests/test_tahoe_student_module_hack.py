"""
Tests for the RED-3616 hack/fix for MAU calculations depending on StudentModule.modified.
"""

from importlib import reload

import pytest
from freezegun import freeze_time


def import_fresh_models():
    """
    Import `lms.djangoapps.courseware.models` and reload it to react to features.
    """
    from lms.djangoapps.courseware import models as courseware_models
    from lms.djangoapps.courseware.tests import factories as courseware_factories
    reload(courseware_models)
    reload(courseware_factories)
    return {
        'courseware_models': courseware_models,
        'courseware_factories': courseware_factories,
    }


def test_is_untouched_by_default_in_celery(settings):
    settings.IS_CELERY_WORKER = True
    courseware_models = import_fresh_models()['courseware_models']
    assert not courseware_models.should_update_student_module_modified_on_save(), 'Should be enabled for celery'


def test_in_updated_by_default_in_http_requests(settings):
    settings.IS_CELERY_WORKER = False
    courseware_models = import_fresh_models()['courseware_models']
    assert courseware_models.should_update_student_module_modified_on_save(), 'Should be disabled in http requests'


def test_can_be_updated_in_celery_if_needed(settings):
    """
    TAHOE_STUDENT_MODULES_DISABLE_MODIFIED_IN_CELERY is on by default but can be turned off via lms FEATURES.
    """
    settings.IS_CELERY_WORKER = True
    settings.FEATURES = {
        **settings.FEATURES,
        'TAHOE_STUDENT_MODULES_DISABLE_MODIFIED_IN_CELERY': False,
    }
    courseware_models = import_fresh_models()['courseware_models']
    assert courseware_models.should_update_student_module_modified_on_save(), 'The feature is configurable'


@pytest.mark.django_db
def test_new_student_module_with_in_celery(settings):
    """
    Ensure that `StudentModule.modified` isn't updated when saving from within a celery task.
    """
    settings.IS_CELERY_WORKER = True
    courseware_factories = import_fresh_models()['courseware_factories']

    with freeze_time('2012-01-14'):
        student_module = courseware_factories.StudentModuleFactory.create()
        assert student_module.created.year == 2012
        assert student_module.modified.year == 2012

    with freeze_time('2020-12-20'):
        student_module.save()
        assert student_module.created.year == 2012
        assert student_module.modified.year == 2012, 'Should not touch `modified` during in celery'


@pytest.mark.django_db
def test_new_student_module_with_in_http_requests(settings):
    """
    Ensure that `StudentModule.modified` _is updated_ when saving from within an HTTP request.
    """
    courseware_factories = import_fresh_models()['courseware_factories']

    with freeze_time('2012-01-14'):
        student_module = courseware_factories.StudentModuleFactory.create()
        assert student_module.created.year == 2012
        assert student_module.modified.year == 2012

    with freeze_time('2020-12-20'):
        student_module.save()
        assert student_module.created.year == 2012
        assert student_module.modified.year == 2020, 'Should update `modified` outside celery'
