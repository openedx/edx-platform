"""
All tests for applications handlers functions
"""
import pytest
from django.contrib.auth.models import Group

from openedx.adg.lms.applications.test.factories import BusinessLineFactory


@pytest.mark.django_db
def test_create_user_group_with_business_line():
    """
    Assert that user group is created when new business line is added
    """
    BusinessLineFactory()
    assert Group.objects.filter(name='foo').exists()


@pytest.mark.django_db
def test_modify_user_group_with_business_line():
    """
    Assert that user group is modified when existing business line is updated
    """
    business_line = BusinessLineFactory()
    business_line.title = 'bar'
    business_line.save()
    assert Group.objects.filter(name='bar').exists() and not Group.objects.filter(name='foo').exists()


@pytest.mark.django_db
def test_delete_user_group_with_business_line():
    """
    Assert that user group is deleted when existing business line is deleted
    """
    business_line = BusinessLineFactory()
    business_line.delete()
    assert not Group.objects.filter(name='foo').exists()
