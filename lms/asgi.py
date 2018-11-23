import os
import channels

os.environ['DJANGO_SETTINGS_MODULE'] = "lms.envs.aws"
os.environ['SERVICE_VARIANT'] = "lms"
channel_layer = channels.asgi.get_channel_layer()
