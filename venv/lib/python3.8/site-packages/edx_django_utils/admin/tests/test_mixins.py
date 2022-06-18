"""
Tests for admin mixins.
"""
import pytest
from django.contrib.admin import ModelAdmin
from django.contrib.admin.sites import AdminSite

from edx_django_utils.admin.mixins import ReadOnlyAdminMixin
from edx_django_utils.admin.tests.models import GenericModel


class ReadOnlyAdmin(ReadOnlyAdminMixin, ModelAdmin):
    """
    Test admin interface which adds the mixin to be tested.
    """
    pass


@pytest.fixture
def site():
    return AdminSite()


@pytest.fixture
def a_request():
    class MockRequest:
        GET = []
    return MockRequest()


@pytest.fixture
def read_only_admin(site):
    return ReadOnlyAdmin(GenericModel, site)


class TestReadOnlyAdminMixin:
    def test_create(self, read_only_admin, a_request):
        assert not read_only_admin.has_add_permission(a_request)

    def test_delete(self, read_only_admin, a_request):
        assert not read_only_admin.has_delete_permission(a_request)

    def test_delete_action(self, read_only_admin, a_request):
        actions = read_only_admin.get_actions(a_request)
        assert 'delete_selected' not in actions

    def test_list_display_links(self, read_only_admin):
        assert read_only_admin.list_display_links is None

    def test_read_only_fields(self, read_only_admin):
        # The GenericModel has three fields plus an Django-added id field - ensure *all* are marked as read-only.
        assert len(read_only_admin.readonly_fields) == 4
