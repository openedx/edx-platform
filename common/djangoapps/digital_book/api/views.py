import logging

from rest_framework import viewsets, status
from rest_framework.response import Response

log = logging.getLogger(__name__)


class DigitalBookViewSet(viewsets.GenericViewSet):
    """
    Endpoint in the Digital Book API to grant access of a user to
    a Digital Book
    """

    def create(self, request):


        #TODO: print something
        log.info(">>> ")

        #TODO: print some aspect of the resquest


        #TODO: return some response
        return Response(
            status=status.HTTP_201_CREATED,
            data={
                'string_data':"very useful unique data",
                'num_data':42,
            }
        )