"""
All tests for applications handlers functions
"""
import pytest
from django.contrib.auth.models import Group

from openedx.adg.lms.applications.tests.factories import BusinessLineFactory


@pytest.mark.django_db
def test_create_user_group_with_business_line():
    """
    Assert that user group is created when new business line is added
    """
    business_line = BusinessLineFactory()
    assert Group.objects.filter(name=business_line.title).exists()


@pytest.mark.django_db
def test_modify_user_group_with_business_line():
    """
    Assert that user group is modified when existing business line is updated
    """
    business_line = BusinessLineFactory()
    business_line.title = 'bar'
    business_line.save()
    assert Group.objects.filter(name=business_line.title).exists()


@pytest.mark.django_db
def test_delete_user_group_with_business_line():
    """
    Assert that user group is deleted when existing business line is deleted
    """
    business_line = BusinessLineFactory()
    business_line.delete()
    assert not Group.objects.filter(name=business_line.title).exists()
