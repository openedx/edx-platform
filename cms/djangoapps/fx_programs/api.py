
"""
API views for Programs
"""

import json
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from openedx.core.lib.api.authentication import BearerAuthentication
from openedx.core.lib.api.permissions import IsStaff
from .models import FxPrograms

class FxProgramsAPI(APIView):

    authentication_classes = (JwtAuthentication, BearerAuthentication,)

    def get(self, request):
        try:
            programs = FxPrograms.objects.all()
            response_dict = {}
            for program in programs:
                program_dict = {
                    "program_id": str(program.program_id),
                    "name": str(program.name),
                    "course_list": str(program.course_list),
                    "id_course_list": str(program.id_course_list),
                    "metadata": program.metadata
                }
                response_dict[str(program.program_id)] = program_dict
            return Response(data=response_dict, status=status.HTTP_200_OK)
        except:
            return Response("The program does not exist", status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):  # lint-amnesty, pylint: disable=missing-function-docstring
        if request.POST["query"] == 'add_course':
            try:
                course_overview = CourseOverview.get_from_id(str(request.POST["course_id"]))
                if course_overview:
                    print('course_overview', course_overview.display_name)
                    program = FxPrograms.objects.get(program_id=request.POST["program_id"])
                    
                    #Update the course to the program
                    program.course_list = f'{program.course_list}{course_overview.display_name},'
                    program.id_course_list = f'{program.id_course_list}{course_overview.id},' 
                    generated_meta =  {
                        "id": str(course_overview.id),
                        "display_name": str(course_overview.display_name),
                        "language": str(course_overview.language),
                        "banner_image_url": str(course_overview.banner_image_url),
                        "course_image_url": str(course_overview.course_image_url),
                        "start_date": str(course_overview.start_date),
                        "end_date": str(course_overview.end_date)
                        }
                    program.metadata[str(course_overview.id)] = generated_meta
                    program.save()
                response_dict = {
                    "new_course": generated_meta
                }
            except CourseOverview.DoesNotExist:
                return Response("Can't delete the course", status=status.HTTP_400_BAD_REQUEST)
        
        if request.POST["query"] == 'delete_course': 
            try:
                program = FxPrograms.objects.get(program_id=request.POST["program_id"])
                response_dict = { 
                    "id_course_delete": str(request.POST["course_id"])
                }
                id_course_to_delete = 0
                new_course_list = ""
                new_id_course_list = ""

                for id, course_id_in_list in enumerate(program.id_course_list.split(",")):
                    if request.POST["course_id"] == course_id_in_list:
                        id_course_to_delete = id
                    else:
                        new_id_course_list += f'{course_id_in_list},'

                for id, course_in_list in enumerate(program.course_list.split(",")):
                    if id_course_to_delete != id:
                        new_course_list += f'{course_in_list},'

                program.course_list = new_course_list[:-1]
                program.id_course_list = new_id_course_list[:-1]
                del program.metadata[request.POST["course_id"]]
                program.save()
                
                return Response(data=response_dict, status=status.HTTP_200_OK)
            except:
                return Response("Can't delete the course", status=status.HTTP_400_BAD_REQUEST)
        return Response(data=response_dict, status=status.HTTP_200_OK)


        