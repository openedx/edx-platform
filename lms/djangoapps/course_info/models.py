# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from model_utils import Choices
from django.core.exceptions import ValidationError
from opaque_keys.edx.django.models import CourseKeyField
from django.utils.translation import ugettext_lazy as _

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

class MainClassification(models.Model):
    SHOW_OPT = Choices((0,'no_show',('No Mostrar')),(1,'only_with_course',('Solo si tiene cursos')),(2,'always',('Siempre')))
    name = models.CharField(max_length=255,verbose_name=_('name'),unique=True)
    sequence = models.IntegerField(verbose_name=_('sequence'))
    show_opt = models.IntegerField(choices=SHOW_OPT,default=0,verbose_name=_('Mostrar'))

    def __str__(self):
        return self.name

    class Meta(object):
        ordering = ('sequence','name',)

class FirstClassification(models.Model):
    name = models.CharField(max_length=255,verbose_name=_('name'),unique=True)
    def __str__(self):
        return self.name
    class Meta(object):
        ordering = ('name',)

class SecondClassification(models.Model):
    name = models.CharField(max_length=255,verbose_name=_('name'),unique=True)
    def __str__(self):
        return self.name
    class Meta(object):
        ordering = ('name',)

class ThirdClassification(models.Model):
    name = models.CharField(max_length=255,verbose_name=_('name'),unique=True)
    def __str__(self):
        return self.name
    class Meta(object):
        ordering = ('name',)

class CourseClassification(models.Model):

    course_id = CourseKeyField(max_length=255, db_index=True, unique=True,verbose_name=_('course'))
    MainClass = models.ForeignKey(MainClassification,verbose_name=u'Clasificación Principal')
    FirstClass = models.ForeignKey(FirstClassification,verbose_name=u'Clasificación 1',blank=True,null=True)
    SecondClass = models.ForeignKey(SecondClassification,verbose_name=u'Clasificación 2',blank=True,null=True)
    ThirdClass = models.ForeignKey(ThirdClassification,verbose_name=u'Clasificación 3',blank=True,null=True)

    class Meta(object):
        ordering = ('course_id',)



