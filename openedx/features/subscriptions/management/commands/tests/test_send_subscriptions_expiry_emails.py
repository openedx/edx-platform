"""
Tests for send_subscriptions_expiry_emails.
"""
from datetime import date, timedelta

from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from openedx.features.subscriptions.api.v1.tests.factories import UserSubscriptionFactory
from openedx.features.subscriptions.models import UserSubscription


class SubscriptionExpiryEmailsTests(TestCase):
    """
    Subscription expiry emails management command tests.
    """
    def test_send_subscriptions_expiry_emails_without_expiry_subscriptions(self):
        """
        Test that send_subscriptions_expiry_emails does not send email if no subscriptions are near expiry or expired.
        """
        UserSubscriptionFactory()
        call_command('send_subscriptions_expiry_emails')
        self.assertEqual(len(mail.outbox), 0)

    def test_send_subscriptions_expiry_emails_for_impending_expiry(self):
        """
        Test that send_subscriptions_expiry_emails sends notification if any subscription is near expiry.
        """
        UserSubscriptionFactory(
            expiration_date=date.today() + timedelta(days=1)
        )
        call_command('send_subscriptions_expiry_emails')
        self.assertEqual(len(mail.outbox), 1)

    def test_send_subscriptions_expiry_emails_for_post_expiry(self):
        """
        Test that send_subscriptions_expiry_emails sends notification if any subscription has expired.
        """
        UserSubscriptionFactory(
            expiration_date=date.today() - timedelta(days=1)
        )
        call_command('send_subscriptions_expiry_emails')
        self.assertEqual(len(mail.outbox), 1)

    def test_send_subscriptions_expiry_emails_for_post_expiry_doesnt_spam(self):
        """
        Test that send_subscriptions_expiry_emails does not send expired subscription notification more than once.
        """
        UserSubscriptionFactory(
            expiration_date=date.today() - timedelta(days=2)
        )
        call_command('send_subscriptions_expiry_emails')
        self.assertEqual(len(mail.outbox), 0)
