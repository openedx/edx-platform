"""
This file contains periodic tasks for global_statistics, which will collect data about Open eDX users
and send this data to appropriate service for further processing.
"""

import json
import requests

from celery.task import task

from django.conf import settings
from django.contrib.sites.models import Site
from xmodule.modulestore.django import modulestore
from student.models import UserProfile
from .models import TokenStorage


@task
def count_data():
    """
    Periodic task function that gathers information about the students amount,
    geographical coordinates of the platform, courses amount and
    makes a POST request with the data to the appropriate service.
    """

    # OEGS settings
    oegs_settings = settings.ENV_TOKENS.get('OPEN_EDX_GLOBAL_STATISTICS')

    # Get IP address of the platform and convert it to latitude, longitude.
    check_ip_url = 'http://freegeoip.net/json'
    ip_data = requests.get(check_ip_url)
    ip_data_json = json.loads(ip_data.text)
    platform_latitude = oegs_settings.get("PLATFORM_LATITUDE")
    platform_longitude = oegs_settings.get("PLATFORM_LONGITUDE")
   
    if platform_latitude and platform_longitude:
        latitude = platform_latitude
        longitude = platform_longitude
    else:
        latitude = ip_data_json['latitude']
        longitude = ip_data_json['longitude']

    # Get students amount within current platform.
    students_amount = UserProfile.objects.count()

    # Get courses amount within current platform.
    courses_amount = len(modulestore().get_courses())

    # Secret token to authorize our platform on remote server.
    secret_token, created = TokenStorage.objects.get_or_create(pk=1)

    # Current edx-platform URL
    platform_url = "https://" + settings.SITE_NAME

    # Predefined in the server settings url to send collected data to.
    # For production or local development.
    if oegs_settings.get('OEGS_PERIODIC_TASK_POST_URL'):
        post_url = oegs_settings.get('OEGS_PERIODIC_TASK_POST_URL')
    else:
        post_url = oegs_settings.get('OEGS_PERIODIC_TASK_POST_URL_LOCAL')

    # Posts desired data volume to receiving server.
    # Data volume depends on server settings.
    statistics_level = oegs_settings.get("STATISTICS_LEVEL")
    
    # Site domain name
    site = Site.objects.get_current()

    if statistics_level == 1:
        data_to_send = requests.post(post_url, data={
            'courses_amount': courses_amount,
            'students_amount': students_amount,
            'latitude': latitude,
            'longitude': longitude,
            'platform_url': platform_url,
            'secret_token': secret_token.secret_token,
            'site': site
            })
