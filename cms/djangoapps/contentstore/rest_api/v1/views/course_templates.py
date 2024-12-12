from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from opaque_keys.edx.keys import CourseKey  # Import CourseKey if using edX
from django.conf import settings
import requests
from openedx.core.lib.api.view_utils import (
    DeveloperErrorViewMixin,
    view_auth_classes,
)
from rest_framework.request import Request
from ..serializers import CourseSerializer, CourseMetadataSerializer


# @view_auth_classes(is_authenticated=True)
class CourseTemplatesListView(DeveloperErrorViewMixin, APIView):
    """
    API endpoint to fetch and return course data from a GitHub repository.

    This view dynamically fetches course data from a specified GitHub repository
    and returns it in a structured JSON format. It processes directories and files
    in the repository to extract course names, ZIP URLs, and metadata files.

    Example URL:
        /api/courses/<course_key_string>/

    Query Parameters:
        course_key_string (str): The course key in the format `org+course+run`.

    Example Response:
    [
        {
            "courses_name": "AI Courses",
            "zip_url": "https://raw.githubusercontent.com/awais786/courses/main/edly/AI%20Courses/course._Rnm_t%20(1).tar.gz",
            "metadata": {
                "course_id": "course-v1:edX+DemoX+T2024",
                "title": "Introduction to Open edX",
                "description": "Learn the fundamentals of the Open edX platform, including how to create and manage courses.",
                "thumbnail": "https://discover.ilmx.org/wp-content/uploads/2024/01/Course-image-2.webp",
                "active": true
            }
        }
    ]

    Raises:
        NotFound: If there is an error fetching data from the repository.

    """
    def get(self, request: Request, course_id: str):
        """
        Handle GET requests to fetch course data.

        Args:
            request: The HTTP request object.
            course_id (str): The course id.

        Returns:
            Response: A structured JSON response containing course data.

        """
        try:
            # Extract organization from course key
            course_key = CourseKey.from_string(course_id)
            organization = course_key.org

            # GitHub repository details. It should come from settings.
            templates_repo_url = f"https://api.github.com/repos/awais786/courses/contents/{organization}"

            # Fetch data from GitHub
            data = fetch_contents(templates_repo_url)
            courses = []
            for directory in data:
                course_data = {'courses_name': directory["name"]}
                contents = fetch_contents(directory["url"])  # Assume directory contains URL to course contents

                for item in contents:
                    if item['name'].endswith('.tar.gz'):  # Check if file is a ZIP file
                        course_data['zip_url'] = item['download_url']
                    elif item['name'].endswith('.json'):  # Check if file is a JSON metadata file
                        course_data['metadata'] = fetch_contents(item['download_url'])

                courses.append(course_data)

            # Serialize and return the data
            serializer = CourseSerializer(courses, many=True)
            return Response(serializer.data)

        except Exception as err:
            raise NotFound(f"Error fetching course data: {str(err)}")


def fetch_contents(url):
    headers = {
        "Authorization": f"token {settings.GITHUB_TOKEN_COURSE_TEMPLATES}",
        "Accept": "application/vnd.github.v3+json",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise error for 4xx/5xx responses
        return response.json()
    except Exception as err:
        return JsonResponseBadRequest({"error": err.message})
