# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

# We're doing something awful here, but it's necessary for the greater good:
from django.contrib.auth.models import User

from instructor.access import allow_access, revoke_access

from ccx_keys.locator import CCXLocator
from lms.djangoapps.ccx.utils import ccx_course

def change_existing_ccx_coaches_to_staff(apps, schema_editor):
	"""
	Modify all coaches of CCX courses so that they have the staff role on the
	CCX course they coach, but retain the CCX Coach role on the parent course.

	Arguments:
		apps (Applications): Apps in edX platform.
		schema_editor (SchemaEditor): For editing database schema (unused)

	"""
	CustomCourseForEdX = apps.get_model('ccx', 'CustomCourseForEdX')
	db_alias = schema_editor.connection.alias
	list_ccx = CustomCourseForEdX.objects.using(db_alias).all()
	for ccx in list_ccx:
		ccx_locator = CCXLocator.from_course_locator(ccx.course_id, unicode(ccx.id))
		with ccx_course(ccx_locator) as course:
			coach = User.objects.get(id=ccx.coach.id)
			allow_access(course, coach, 'staff', send_email=False)
			revoke_access(course, coach, 'ccx_coach', send_email=False)

def revert_ccx_staff_to_coaches(apps, schema_editor):
	"""
	Modify all staff on CCX courses so that they no longer have the staff role
	on the course that they coach.

	Arguments:
		apps (Applications): Apps in edX platform.
		schema_editor (SchemaEditor): For editing database schema (unused)

	"""
	CustomCourseForEdX = apps.get_model('ccx', 'CustomCourseForEdX')
	db_alias = schema_editor.connection.alias
	list_ccx = CustomCourseForEdX.objects.using(db_alias).all()
	for ccx in list_ccx:
		ccx_locator = CCXLocator.from_course_locator(ccx.course_id, unicode(ccx.id))
		with ccx_course(ccx_locator) as course:
			coach = User.objects.get(id=ccx.coach.id)
			allow_access(course, coach, 'ccx_coach', send_email=False)
			revoke_access(course, coach, 'staff', send_email=False)

class Migration(migrations.Migration):

	dependencies = [
		('ccx', '0001_initial'),
		('ccx', '0002_customcourseforedx_structure_json'),
		('ccx', '0003_add_master_course_staff_in_ccx'),
	]

	operations = [
		migrations.RunPython(
			code=change_existing_ccx_coaches_to_staff,
			reverse_code=revert_ccx_staff_to_coaches
		)
	]
