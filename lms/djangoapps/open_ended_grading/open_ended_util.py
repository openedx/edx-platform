from django.conf import settings

def get_controller_url():
    peer_grading_url = settings.PEER_GRADING_INTERFACE
    split_url = peer_grading_url.split("/")
    controller_url = "http://" + split_url[2] + "/grading_controller"
    return controller_url
