from django.contrib.auth.models import User
from lettuce import step, world
from notification_prefs import NOTIFICATION_PREF_KEY
from user_api.models import UserPreference


USERNAME = "robot"
UNSUB_TOKEN = "av9E-14sAP1bVBRCPbrTHQ=="


@step(u"I have notifications enabled")
def enable_notifications(step_):
    user = User.objects.get(username=USERNAME)
    UserPreference.objects.create(user=user, key=NOTIFICATION_PREF_KEY, value=UNSUB_TOKEN)


@step(u"I access my unsubscribe url")
def access_unsubscribe_url(step_):
    world.visit("/notification_prefs/unsubscribe/{0}/".format(UNSUB_TOKEN))


@step(u"my notifications should be disabled")
def notifications_should_be_disabled(step_):
    user = User.objects.get(username=USERNAME)
    assert not UserPreference.objects.filter(user=user, key=NOTIFICATION_PREF_KEY).exists()
