"""
Tests for customization in the admin.py for Tahoe.
"""
from mock import patch, Mock

from organizations.models import Organization
from student.admin import RegistrationAdmin


@patch('student.admin.get_single_user_organization', Mock(side_effect=Organization.DoesNotExist))
def test_activation_link_no_org():
    """
    Missing organizations are handled gracefully.
    """
    registration = Mock(user=Mock(is_active=False))
    admin = RegistrationAdmin(Mock(), Mock())
    link = admin.activation_link(registration)
    assert link == 'Error: missing organization.'


def test_activation_link_learner_is_active():
    """
    Don't show the link for active learners.
    """
    registration = Mock(user=Mock(is_active=True))
    admin = RegistrationAdmin(Mock(), Mock())
    link = admin.activation_link(registration)
    assert link == 'Learner is active.'


@patch('student.admin.get_single_user_organization', Mock())
@patch('student.admin.get_site_by_organization', Mock(return_value=Mock(domain='somesite.org')))
def test_activation_link():
    """
    The link prints well and only for copying.
    """
    registration = Mock(user=Mock(is_active=False), activation_key='xyz')
    admin = RegistrationAdmin(Mock(), Mock())

    link = admin.activation_link(registration)
    assert '//somesite.org/activate/xyz' in link
    assert 'return false;' in link, 'Should prevent clicking'
    assert 'Email confirmation link' in link
