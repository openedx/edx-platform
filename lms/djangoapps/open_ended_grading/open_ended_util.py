from django.conf import settings
import logging

log=logging.getLogger(__name__)

def get_controller_url():
    peer_grading_url = settings.PEER_GRADING_INTERFACE['url']
    split_url = peer_grading_url.split("/")
    controller_url = "http://" + split_url[2] + "/grading_controller"
    controller_settings=settings.PEER_GRADING_INTERFACE.copy()
    controller_settings['url'] = controller_url
    return controller_settings
