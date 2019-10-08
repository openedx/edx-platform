# encoding: utf-8
"""Tests of Management Commands """
from __future__ import unicode_literals

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from lms.djangoapps.onboarding.helpers import get_current_utc_date
from lms.djangoapps.onboarding.models import OrganizationMetricUpdatePrompt, Organization


class OrganizationMetrics(TestCase):
    """Test Command to update Organization Metrics"""

    def test_update_org_today_metrics(self):
        user = User(username='usman', email='usman@gmail.com', first_name='usman',
                    last_name='khan', password='abc123', is_active=True)
        user.save()
        org = Organization(label='Home')
        org.save()
        today = get_current_utc_date()
        save_prompt(user, org, today)

        today_result = {
            "latest_metric_submission": today,
            "year": False,
            "year_month": False,
            "year_three_month": False,
            "year_six_month": False,
        }

        call_command('update_org_metric_prompts')
        today_metrics = OrganizationMetricUpdatePrompt.objects.filter(latest_metric_submission=today).values(
            "latest_metric_submission", "year", "year_month", "year_three_month", "year_six_month").first()
        self.assertEqual(today_metrics['year'], False)
        self.assertEqual(today_metrics['year_month'], False)
        self.assertEqual(today_metrics['year_three_month'], False)
        self.assertEqual(today_metrics['year_six_month'], False)

    def test_update_org_year_old_metrics(self):
        user2 = User(username='muak', email='muak@gmail.com', first_name='usman',
                     last_name='arshad', password='abc123', is_active=True)
        user2.save()

        org = Organization(label='Home')
        org.save()

        today = get_current_utc_date()
        one_year_old_date = today - timedelta(days=366)

        save_prompt(user2, org, one_year_old_date)

        one_year_old_result = {
            "latest_metric_submission": one_year_old_date,
            "year": True,
            "year_month": False,
            "year_three_month": False,
            "year_six_month": False,
        }

        call_command('update_org_metric_prompts')
        one_year_old_metrics = OrganizationMetricUpdatePrompt.objects.filter(
            latest_metric_submission=one_year_old_date).values(
            "latest_metric_submission", "year", "year_month", "year_three_month", "year_six_month").first()
        self.assertEqual(one_year_old_metrics['year'], True)
        self.assertEqual(one_year_old_metrics['year_month'], False)
        self.assertEqual(one_year_old_metrics['year_three_month'], False)
        self.assertEqual(one_year_old_metrics['year_six_month'], False)

    def test_update_org_year_three_months_old_metrics(self):
        user3 = User(username='ali', email='ali@gmail.com', first_name='ali',
                     last_name='khan', password='abc123', is_active=True)
        user3.save()

        org = Organization(label='Home')
        org.save()

        today = get_current_utc_date()
        one_year_three_months_old_date = today - timedelta(days=466)

        save_prompt(user3, org, one_year_three_months_old_date)

        one_year_three_month_old_result = {
            "latest_metric_submission": one_year_three_months_old_date,
            "year": True,
            "year_month": True,
            "year_three_month": True,
            "year_six_month": False,
        }

        call_command('update_org_metric_prompts')
        one_year_three_months_old_metrics = OrganizationMetricUpdatePrompt.objects.filter(
            latest_metric_submission=one_year_three_months_old_date).values(
            "latest_metric_submission", "year", "year_month", "year_three_month", "year_six_month").first()
        self.assertEqual(one_year_three_months_old_metrics['year'], True)
        self.assertEqual(one_year_three_months_old_metrics['year_month'], True)
        self.assertEqual(one_year_three_months_old_metrics['year_three_month'], True)
        self.assertEqual(one_year_three_months_old_metrics['year_six_month'], False)

    def test_update_org_year_six_months_old_metrics(self):
        user4 = User(username='john', email='john@gmail.com', first_name='John',
                     last_name='wick', password='abc123', is_active=True)
        user4.save()

        org = Organization(label='Home')
        org.save()

        today = get_current_utc_date()
        one_year_six_months_old_date = today - timedelta(days=550)

        save_prompt(user4, org, one_year_six_months_old_date)

        one_year_six_month_old_result = {
            "latest_metric_submission": one_year_six_months_old_date,
            "year": True,
            "year_month": True,
            "year_three_month": True,
            "year_six_month": True,
        }

        call_command('update_org_metric_prompts')
        one_year_six_months_old_metrics = OrganizationMetricUpdatePrompt.objects.filter(
            latest_metric_submission=one_year_six_months_old_date).values(
            "latest_metric_submission", "year", "year_month", "year_three_month", "year_six_month").first()
        self.assertEqual(one_year_six_months_old_metrics['year'], True)
        self.assertEqual(one_year_six_months_old_metrics['year_month'], True)
        self.assertEqual(one_year_six_months_old_metrics['year_three_month'], True)
        self.assertEqual(one_year_six_months_old_metrics['year_six_month'], True)


def save_prompt(user, org, date):
    prompt = OrganizationMetricUpdatePrompt(responsible_user=user,
                                            org=org,
                                            latest_metric_submission=date,
                                            year=False,
                                            year_month=False,
                                            year_three_month=False,
                                            year_six_month=False
                                            )
    prompt.save()
    return prompt


def get_expected_org_metric_update_prompts(current_date):
    return [
        {
            "latest_metric_submission": current_date,
            "year": False,
            "year_month": False,
            "year_three_month": False,
            "year_six_month": False,
        },
        {
            "latest_metric_submission": current_date - timedelta(days=366),
            "year": True,
            "year_month": False,
            "year_three_month": False,
            "year_six_month": False,
        },
        {
            "latest_metric_submission": current_date - timedelta(days=466),
            "year": True,
            "year_month": True,
            "year_three_month": True,
            "year_six_month": False,
        }
    ]
