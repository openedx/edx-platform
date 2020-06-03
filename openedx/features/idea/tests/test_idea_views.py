# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ddt import ddt, file_data
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status

from common.test.utils import MockS3Mixin
from lms.djangoapps.onboarding.helpers import COUNTRIES
from lms.djangoapps.onboarding.tests.factories import OrganizationFactory, UserFactory
from openedx.features.philu_utils.tests.mixins import PhiluThemeMixin

from ..models import Idea


class ChallengeViewTests(PhiluThemeMixin, TestCase):

    def test_get_idea_challange_page(self):
        response = self.client.get(reverse('challenge-landing'))
        self.assertEqual(response.status_code, 200)

    def test_get_idea_listing_page(self):
        response = self.client.get(reverse('idea-listing'))
        self.assertEqual(response.status_code, 200)

    def test_get_idea_details_page(self):
        response = self.client.get(reverse('idea-details', kwargs=dict(pk=1)))
        self.assertEqual(response.status_code, 200)


@ddt
class CreateIdeaViewTest(PhiluThemeMixin, MockS3Mixin, TestCase):
    """Test idea creating view without pre-filling any field"""

    def setUp(self):
        super(CreateIdeaViewTest, self).setUp()
        self.user = UserFactory()
        self.user.set_password('password')
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password='password')

    def test_login_required_to_create_idea(self):
        """Idea creation form must need login"""
        response = Client().get(reverse('idea-create'))
        self.assertRedirects(
            response,
            '{sign_in}?next={next_url}'.format(sign_in=reverse('signin_user'), next_url=reverse('idea-create'))
        )

    def test_create_ideas_show_form_without_pre_filled_data(self):
        """Show idea creation form successfully, without pre filled data"""
        response = self.client.get(reverse('idea-create'))
        form_data = response.context_data.get('form')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(form_data.initial.get('city'))
        self.assertIsNone(form_data.initial.get('country'))
        self.assertIsNone(form_data.initial.get('organization_name'))
        self.assertEqual(form_data.initial.get('user'), self.user)

    @file_data('data/test_data_idea.json')
    def test_create_ideas_submit_form_without_pre_filled_data(self, idea_form_data):
        """
        Submit idea creation form successfully, without pre-filled data. Assert that new idea is created along with
        new organization and current user is the first learner. Also city and country added to user's profile. Also
        assert that form submission fails if required fields are empty.
        """
        idea_form_data = idea_form_data[0]
        response = self.client.post(reverse('idea-create'), idea_form_data)

        if idea_form_data.get('idea-organization_name') and idea_form_data.get('idea-organization_mission'):
            ideas = Idea.objects.all()
            self.assertEqual(len(ideas), 1)
            idea = ideas.first()

            updated_user = User.objects.get(username=self.user.username)
            self.assertEqual(idea.city, updated_user.profile.city)
            self.assertEqual(idea.country, updated_user.profile.country)
            self.assertEqual(idea.organization, updated_user.extended_profile.organization)
            self.assertEqual(idea.user, updated_user)
            self.assertTrue(updated_user.extended_profile.is_first_learner)
            self.assertRedirects(response, reverse('idea-listing'))
        else:
            # required filed empty
            form_data = response.context_data.get('form')
            self.assertFalse(form_data.is_valid())


@ddt
class CreateIdeaPreFilledViewTest(PhiluThemeMixin, MockS3Mixin, TestCase):
    """Test idea creating view with pre-filled fields"""

    def setUp(self):
        super(CreateIdeaPreFilledViewTest, self).setUp()
        self.user = UserFactory(
            profile__city='karachi',
            profile__country='PK',
            extended_profile__organization=OrganizationFactory(label='test org')
        )
        self.user.set_password('password')
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password='password')

    def test_create_idea_show_form_with_pre_filled_data(self):
        """Show idea creation form successfully, with pre filled data from user profile"""
        response = self.client.get(reverse('idea-create'))

        form_data = response.context_data.get('form')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(form_data.initial.get('city'), self.user.profile.city)
        self.assertEqual(form_data.initial.get('country'), self.user.profile.country)
        self.assertEqual(form_data.initial.get('organization_name'), self.user.extended_profile.organization.label)
        self.assertEqual(form_data.initial.get('user'), self.user)

    @file_data('data/test_data_idea.json')
    def test_create_ideas_pre_filled_form_submission(self, idea_form_data):
        """
        Submit idea creation form successfully, with pre-filled data. Assert that new idea is created along with
        same previous organization. Also assert that form submission fails if required fields are empty.
        """
        idea_form_data = idea_form_data[0]
        response = self.client.post(reverse('idea-create'), idea_form_data)

        if idea_form_data.get('idea-organization_mission'):
            ideas = Idea.objects.all()
            self.assertEqual(len(ideas), 1)
            idea = ideas.first()

            self.assertEqual(idea.city, self.user.profile.city)
            self.assertEqual(idea.country, self.user.profile.country)
            self.assertEqual(idea.organization, self.user.extended_profile.organization)
            self.assertEqual(idea.user, self.user)
            self.assertRedirects(response, reverse('idea-listing'))
        else:
            # required filed empty
            form_data = response.context_data.get('form')
            self.assertFalse(form_data.is_valid())
