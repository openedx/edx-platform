"""
All the tests related to the MultilingualCourseGroupAdmin
"""
import pytest

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.applications.admin import MultilingualCourseGroupAdmin


@pytest.mark.django_db
def test_multilingual_course_group_admin_get_form_widgets(
    multilingual_course_group_admin_instance, course_group, request
):
    """
    Test that the MultilingualCourseGroupAdmin has add, remove and change widget permission restricted for
    BusinessLine foreign key field
    """
    request.user = UserFactory(is_superuser=True)
    form_class = MultilingualCourseGroupAdmin.get_form(
        multilingual_course_group_admin_instance, request, course_group
    )
    form = form_class()

    field = form.base_fields['business_line_prerequisite']
    assert not field.widget.can_add_related
    assert not field.widget.can_change_related
    assert not field.widget.can_delete_related
