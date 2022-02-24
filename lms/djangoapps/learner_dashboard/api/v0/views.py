""" API v0 views. """

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from openedx.core.djangoapps.programs.utils import (
    get_certificates,
    get_industry_and_credit_pathways,
    get_program_urls,
    get_program_and_course_data
)


class ProgramProgressDetailView(APIView):
    """
        **Use Case**

            * Get progress details of a learner enrolled in a program.

        **Example Request**

            GET api/dashboard/v0/programs/{program_uuid}/progress_details/

        **GET Parameters**

            A GET request must include the following parameters.

            * program_uuid: A string representation of uuid of the program.

        **GET Response Values**

            If the request for information about the program is successful, an HTTP 200 "OK" response
            is returned.

            The HTTP 200 response has the following values.

            * urls: Urls to enroll/purchase a course or view program record.

            * program_data: Holds meta information about the program.

            * course_data: Learner's progress details for all courses in the program (in-progress/remaining/completed).

            * certificate_data: Details about learner's certificates status for all courses in the program and the
                program itself.

            * industry_pathways: Industry pathways for the program, comes under additional credit opportunities.

            * credit_pathways: Credit pathways for the program, comes under additional credit opportunities.

        **Example GET Response**

            {
                "urls": {
                    "program_listing_url": "/dashboard/programs/",
                    "track_selection_url": "/course_modes/choose/",
                    "commerce_api_url": "/api/commerce/v0/baskets/",
                    "buy_button_url": "http://ecommerce.com/basket/add/?",
                    "program_record_url": "https://credentials.example.com/records/programs/121234235525242344"
                },
                "program_data": {
                    "uuid": "a156a6e2-de91-4ce7-947a-888943e6b12a",
                    "title": "edX Demonstration Program",
                    "subtitle": "",
                    "type": "MicroMasters",
                    "status": "active",
                    "marketing_slug": "demo-program",
                    "marketing_url": "micromasters/demo-program",
                    "authoring_organizations": [],
                    "card_image_url": "http://edx.devstack.lms:18000/asset-v1:edX+DemoX+Demo_Course.jpg",
                    "is_program_eligible_for_one_click_purchase": false,
                    "pathway_ids": [
                        1,
                        2
                    ],
                    "is_learner_eligible_for_one_click_purchase": false,
                    "skus": ["AUD122342"],
                },
                "course_data": {
                    "uuid": "a156a6e2-de91-4ce7-947a-888943e6b12a",
                    "completed": [],
                    "in_progress": [],
                    "not_started": [
                        {
                            "key": "edX+DemoX",
                            "uuid": "fe1a9ad4-a452-45cd-80e5-9babd3d43f96",
                            "title": "Demonstration Course",
                            "course_runs": [],
                            "entitlements": [],
                            "owners": [],
                            "image": "",
                            "short_description": "",
                            "type": "457f07ec-a78f-45b4-ba09-5fb176520d8a",
                        }
                    ],
                },
                "certificate_data": [{
                    "type": "course",
                    "title": "edX Demo Course",
                    'url': "/certificates/6e57d3cce8e34cfcb60bd8e8b04r07e0",
                }],
                "industry_pathways": [
                    {
                        "id": 2,
                        "uuid": "1b8fadf1-f6aa-4282-94e3-325b922a027f",
                        "name": "Demo Industry Pathway",
                        "org_name": "edX",
                        "email": "edx@edx.com",
                        "description": "Sample demo industry pathway",
                        "destination_url": "http://rit.edu/online/pathways/gtx-analytics-essential-tools-methods",
                        "pathway_type": "industry",
                        "program_uuids": [
                            "a156a6e2-de91-4ce7-947a-888943e6b12a"
                        ]
                    }
                ],
                "credit_pathways": [
                    {
                        "id": 1,
                        "uuid": "86b9701a-61e6-48a2-92eb-70a824521c1f",
                        "name": "Demo Credit Pathway",
                        "org_name": "edX",
                        "email": "edx@edx.com",
                        "description": "Sample demo credit pathway!",
                        "destination_url": "http://rit.edu/online/pathways/ritx-design-thinking",
                        "pathway_type": "credit",
                        "program_uuids": [
                            "a156a6e2-de91-4ce7-947a-888943e6b12a"
                        ]
                    }
                ]
            }
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )

    permission_classes = (IsAuthenticated,)

    def get(self, request, program_uuid):
        """
        Retrieves progress details of a user in a specified program.

        Args:
            request (Request): Django request object.
            program_uuid (string): URI element specifying uuid of the program.

        Return:
        """
        user = request.user
        site = request.site
        program_data, course_data = get_program_and_course_data(site, user, program_uuid)
        if not program_data:
            return Response(
                status=404,
                data={'error_code': 'No program data available.'}
            )

        certificate_data = get_certificates(user, program_data)
        program_data.pop('courses')

        urls = get_program_urls(program_data)
        if not certificate_data:
            urls['program_record_url'] = None

        industry_pathways, credit_pathways = get_industry_and_credit_pathways(program_data, site)

        return Response(
            {
                'urls': urls,
                'program_data': program_data,
                'course_data': course_data,
                'certificate_data': certificate_data,
                'industry_pathways': industry_pathways,
                'credit_pathways': credit_pathways,
            }
        )
