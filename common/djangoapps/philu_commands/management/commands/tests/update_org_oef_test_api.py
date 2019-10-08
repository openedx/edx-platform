# encoding: utf-8
"""Tests of Management Commands """
from __future__ import unicode_literals

from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth.models import User

from lms.djangoapps.oef.models import OrganizationOefUpdatePrompt
from lms.djangoapps.onboarding.helpers import get_current_utc_date
from lms.djangoapps.onboarding.models import Organization


class OrganizationOef(TestCase):
    """Test Command to update Organization OEF Prompts"""

    def test_update_org_today_oef(self):
        user = User(username='usman', email='usman@gmail.com', first_name='usman',
                    last_name='khan', password='abc123', is_active=True)
        user.save()
        org = Organization(label='Home')
        org.save()
        today = get_current_utc_date()
        save_oef_prompt(user, org, today)

        call_command('update_org_oef_prompts')
        today_oef_prompts = OrganizationOefUpdatePrompt.objects.filter(latest_finish_date=today).values(
            "latest_finish_date", "year").first()

        """ Should be False for today """
        self.assertEqual(today_oef_prompts['year'], False)

    def test_update_org_one_year_old_oef(self):
        user = User(username='muak', email='muak@gmail.com', first_name='usman',
                    last_name='arshad', password='abc123', is_active=True)
        user.save()
        org = Organization(label='Home')
        org.save()
        today = get_current_utc_date()
        one_year_old_date = today - timedelta(days=366)
        save_oef_prompt(user, org, one_year_old_date)

        call_command('update_org_oef_prompts')
        one_year_old_oef_prompts = OrganizationOefUpdatePrompt.objects.filter(
            latest_finish_date=one_year_old_date).values("latest_finish_date", "year").first()

        """ Should be True for one year old date """
        self.assertEqual(one_year_old_oef_prompts['year'], True)


def save_oef_prompt(user, org, date):
    prompt = OrganizationOefUpdatePrompt(responsible_user=user,
                                         org=org,
                                         latest_finish_date=date,
                                         year=False,
                                         )
    prompt.save()
