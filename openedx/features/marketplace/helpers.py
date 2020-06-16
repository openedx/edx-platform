from django.conf import settings


def get_connect_url(marketplace_request, request_user):
    """
    Connecting user with Org Admin/First Learner via NodeBB Chat
        1: If Organization admin is not present then connect with the first learner.
        2: If Organization(orphan organization) admin and first learner both are
           not present then connect user with the marketplace request creator.
        3: In case of requester is the admin/first learner of organization
           button should be grayed out and disabled.
    :param marketplace_request: marketplace request item
    :param request_user: request user object
    """
    chat_url = '{nodebb_end_point}/chat/{username}'
    responsible_user = marketplace_request.organization.admin or marketplace_request.organization.first_learner \
                       or marketplace_request.user
    if responsible_user.username != request_user.username:
        connect_url = chat_url.format(nodebb_end_point=settings.NODEBB_ENDPOINT, username=responsible_user.username)
    else:
        connect_url = None

    return connect_url
