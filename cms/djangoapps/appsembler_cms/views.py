import logging

from django.contrib.auth.models import User

from rest_framework import status

from cms.djangoapps.contentstore.utils import reverse_course_url
from cms.djangoapps.contentstore.views.course import create_new_course_in_store
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from xmodule.modulestore.django import modulestore

from appsembler_lms.permissions import SecretKeyPermission
from .serializers import CreateCourseSerializer

logger = logging.getLogger(__name__)
APPSEMBLER_EMAIL = 'support@appsembler.com'


class CreateCourseAPIView(GenericAPIView):
    permission_classes = (SecretKeyPermission,)
    serializer_class = CreateCourseSerializer

    def post(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(email=serializer.data.get('email'))
            except User.DoesNotExist:
                message = "User does not exist in academy.appsembler.com"
                return Response(status=status.HTTP_404_NOT_FOUND, data=message)

            try:
                store_for_new_course = modulestore().default_modulestore.get_modulestore_type()
                org = user.profile.organization.key
                number = "{}101".format(user.username)
                run = "CurrentTerm"
                fields = {
                    "display_name": "Your First Course"
                }
                new_course = create_new_course_in_store(store_for_new_course, user, org,
                                                        number, run, fields)
                new_course_url = reverse_course_url('course_handler', new_course.id)
                response_data = {
                    'course_url': new_course_url
                }
                return Response(status=status.HTTP_201_CREATED, data=response_data)
            except:
                message = "Unable to create new course."
                logger.error(message)
        return Response(status=status.HTTP_400_BAD_REQUEST)

create_course_endpoint = CreateCourseAPIView.as_view()
