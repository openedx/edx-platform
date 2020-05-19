# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from model_utils.models import TimeStampedModel


class SmartReferral(TimeStampedModel):
    user = models.ForeignKey(User, related_name='smart_referrals', related_query_name='smart_referral',
                             on_delete=models.CASCADE)
    contact_email = models.EmailField(max_length=255)
    is_contact_reg_completed = models.BooleanField(default=False, verbose_name='Is contact registration completed')

    class Meta(object):
        app_label = 'smart_referral'

    def __unicode__(self):
        return '{user} referred {contact}'.format(user=self.user.username, contact=self.contact_email)
