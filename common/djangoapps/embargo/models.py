"""
Models for embargoing countries
"""
from django.db import models

from config_models.models import ConfigurationModel


class EmbargoConfig(ConfigurationModel):
	"""
	Configuration for the embargo feature
	"""
	embargoed_countries = models.TextField(
		blank=True,
		help_text="A comma-separated list of country codes that fall under U.S. embargo restrictions"
	)

	embargoed_courses = models.TextField(
		blank = True,
		help_text = "A comma-separated list of course IDs that we are enforcing the embargo for"
	)

	@property
	def embargoed_countries_list(self):
		if not self.embargoed_countries.strip():
			return []
		return [country.strip() for country in self.embargoed_countries.split(',')]

	@property
	def embargoed_courses_list(self):
		if not self.embargoed_courses.strip():
			return []
		return [course.strip() for course in self.embargoed_courses.split(',')]