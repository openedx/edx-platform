"""
Utility functions for validating forms
"""
from django import forms
from django.template import loader
from django.utils.http import int_to_base36
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.hashers import UNUSABLE_PASSWORD
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site

from edxmako.shortcuts import render_to_string


class PasswordResetFormNoActive(PasswordResetForm):
    def clean_email(self):
        """
        This is a literal copy from Django 1.4.5's django.contrib.auth.forms.PasswordResetForm
        Except removing the requirement of active users
        Validates that a user exists with the given email address.
        """
        email = self.cleaned_data["email"]
        #The line below contains the only change, removing is_active=True
        self.users_cache = User.objects.filter(email__iexact=email)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        if any((user.password == UNUSABLE_PASSWORD)
               for user in self.users_cache):
            raise forms.ValidationError(self.error_messages['unusable'])
        return email

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             html_email_template_name='registration/password_reset_email_html.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        """
        This is a copy from Django 1.4.5's django.contrib.auth.forms.PasswordResetForm
        Except it adds support for multipart email
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        from mail import send_mail
        from django.conf import settings
        for user in self.users_cache:
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            context = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            subject = loader.render_to_string(subject_template_name, context)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, context)
            email_html = None
            if (settings.FEATURES.get('ENABLE_MULTIPART_EMAIL')):
                email_html = render_to_string(html_email_template_name, context)
            send_mail(subject, email, from_email, [user.email], html_message=email_html)
