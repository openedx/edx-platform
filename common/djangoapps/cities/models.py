# -*- coding: utf-8 -*-

"""
Models for Cities, States Information

Migration Notes

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms schemamigration student --auto description_of_your_change
"""

from django.db import models
from django.utils.translation import ugettext as _

from django_countries import CountryField

class State(models.Model):
    """
    TODO: doc
    """
    code = models.CharField(max_length=8, verbose_name=_('Code'))
    name = models.CharField(max_length=128, verbose_name=_('State'))
    country = CountryField()

    def __unicode__(self):
        return u'%s, %s' % (self.name, self.country.name)

    class Meta:
        verbose_name_plural = _('States')
    

class City(models.Model):
    """
    TODO: doc
    """
    name = models.CharField(max_length=64, verbose_name=_('City'))
    code = models.CharField(max_length=64, verbose_name=_('Code'))
    state = models.ForeignKey(State, null=True, blank=True)

    def __unicode__(self):
        return u'%s, %s' % (self.name, self.state)

    class Meta:
        verbose_name_plural = _('Cities')
    
