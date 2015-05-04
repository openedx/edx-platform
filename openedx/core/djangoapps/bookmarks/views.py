import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class BoomarksView(APIView):
    """

    """
    def get(self, request):
        response = {
            "id": "43882bd86e3d4167a80f7fb7bb199cbf",
            "course_id": "MITx/4.605x_2/3T2014",
            "usage_id": "i4x://RiceX/BIOC300.1x/openassessment/cf4c1de230af407fa214905b90aace57",
            "display_name": "A Global History of Architecture: Part 1",
            "path": [
                {
                    "usage_id": "i4x://RiceX/BIOC300.1x/chapter/cf4c1de2efmveoirm1490e57",
                    "display_name": "Week 1"
                },
                {
                    "usage_id": "i4x://RiceX/BIOC300.1x/sequential/foivmeiormoeriv4905b90aace57",
                    "display_name": "Reflection"
                }
            ],
            "created": "2014-09-23T14:00:00Z"
        }

        responses = {'results': []}

        for index in range(3):
            responses['results'].append(dict(response))
            responses['results'][index]['id'] = index

        return Response(responses)

    def post(self, request, username):
        return Response(status=status.HTTP_404_NOT_FOUND)
