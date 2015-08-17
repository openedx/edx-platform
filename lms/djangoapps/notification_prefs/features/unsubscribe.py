from django.contrib.auth.models import User
from lettuce import step, world
from notification_prefs import NOTIFICATION_PREF_KEY
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference, get_user_preference


USERNAME = "robot"
UNSUB_TOKEN = "av9E-14sAP1bVBRCPbrTHQ=="


@step(u"I have notifications enabled")
def enable_notifications(step_):
    user = User.objects.get(username=USERNAME)
    set_user_preference(user, NOTIFICATION_PREF_KEY, UNSUB_TOKEN)


@step(u"I access my unsubscribe url")
def access_unsubscribe_url(step_):
    world.visit("/notification_prefs/unsubscribe/{0}/".format(UNSUB_TOKEN))


@step(u"my notifications should be disabled")
def notifications_should_be_disabled(step_):
    user = User.objects.get(username=USERNAME)
    assert not get_user_preference(user, NOTIFICATION_PREF_KEY)
