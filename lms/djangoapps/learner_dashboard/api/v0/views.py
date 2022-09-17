""" API v0 views. """

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from enterprise.models import EnterpriseCourseEnrollment
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.track import segment
from openedx.core.djangoapps.programs.utils import (
    ProgramProgressMeter,
    get_certificates,
    get_industry_and_credit_pathways,
    get_program_and_course_data,
    get_program_urls
)
from openedx.core.djangoapps.catalog.utils import get_course_data
from lms.djangoapps.learner_dashboard.api.utils import get_personalized_course_recommendations


class Programs(APIView):
    """
        **Use Case**

            * Get a list of all programs in which request user has enrolled.

        **Example Request**

            GET /api/dashboard/v0/programs/{enterprise_uuid}/

        **GET Parameters**

            A GET request must include the following parameters.

            * enterprise_uuid: UUID of an enterprise customer.

        **Example GET Response**

        [
            {
                "uuid": "ff41a5eb-2a73-4933-8e80-a1c66068ed2c",
                "title": "edX Demonstration Program",
                "type": "MicroMasters",
                "banner_image": {
                    "large": {
                        "url": "http://localhost:18381/media/programs/banner_images/ff41a5eb-2a73-4933-8e80.large.jpg",
                        "width": 1440,
                        "height": 480
                    },
                    "medium": {
                        "url": "http://localhost:18381/media/programs/banner_images/ff41a5eb-2a73-4933-8e80.medium.jpg",
                        "width": 726,
                        "height": 242
                    },
                    "small": {
                        "url": "http://localhost:18381/media/programs/banner_images/ff41a5eb-2a73-4933-8e80.small.jpg",
                        "width": 435,
                        "height": 145
                    },
                    "x-small": {
                        "url": "http://localhost:18381/media/programs/banner_images/ff41a5eb-2a73-4933-8e8.x-small.jpg",
                        "width": 348,
                        "height": 116
                    }
                },
                "authoring_organizations": [
                    {
                        "key": "edX"
                    }
                ],
                "progress": {
                    "uuid": "ff41a5eb-2a73-4933-8e80-a1c66068ed2c",
                    "completed": 0,
                    "in_progress": 0,
                    "not_started": 2
                }
            }
        ]
    """

    authentication_classes = (JwtAuthentication, SessionAuthentication,)

    permission_classes = (IsAuthenticated,)

    def get(self, request, enterprise_uuid):
        """
        Return a list of a enterprise learner's all enrolled programs with their progress.

        Args:
            request (Request): DRF request object.
            enterprise_uuid (string): UUID of an enterprise customer.
        """
        user = request.user

        enrollments = self._get_enterprise_course_enrollments(enterprise_uuid, user)
        # return empty reponse if no enterprise enrollments exists for a user
        if not enrollments:
            return Response([])

        meter = ProgramProgressMeter(
            request.site,
            user,
            enrollments=enrollments,
            mobile_only=False,
            include_course_entitlements=False
        )
        engaged_programs = meter.engaged_programs
        progress = meter.progress(programs=engaged_programs)
        programs = self._extract_minimal_required_programs_data(engaged_programs)
        programs = self._combine_programs_data_and_progress(programs, progress)

        return Response(programs)

    def _combine_programs_data_and_progress(self, programs_data, programs_progress):
        """
        Return the combined program and progress data so that api clinet can easily process the data.
        """
        for program_data in programs_data:
            program_progress = next((item for item in programs_progress if item['uuid'] == program_data['uuid']), None)
            program_data['progress'] = program_progress

        return programs_data

    def _extract_minimal_required_programs_data(self, programs_data):
        """
        Return only the minimal required program data need for program listing page.
        """
        def transform(key, value):
            transformers = {'authoring_organizations': transform_authoring_organizations}

            if key in transformers:
                return transformers[key](value)

            return value

        def transform_authoring_organizations(authoring_organizations):
            """
            Extract only the required data for `authoring_organizations` for a program
            """
            transformed_authoring_organizations = []
            for authoring_organization in authoring_organizations:
                transformed_authoring_organizations.append(
                    {
                        'key': authoring_organization['key'],
                        'logo_image_url': authoring_organization['logo_image_url']
                    }
                )

            return transformed_authoring_organizations

        program_data_keys = ['uuid', 'title', 'type', 'banner_image', 'authoring_organizations']
        programs = []
        for program_data in programs_data:
            program = {}
            for program_data_key in program_data_keys:
                program[program_data_key] = transform(program_data_key, program_data[program_data_key])

            programs.append(program)

        return programs

    def _get_enterprise_course_enrollments(self, enterprise_uuid, user):
        """
        Return only enterprise enrollments for a user.
        """
        enterprise_enrollment_course_ids = list(EnterpriseCourseEnrollment.objects.filter(
            enterprise_customer_user__user_id=user.id,
            enterprise_customer_user__enterprise_customer__uuid=enterprise_uuid,
        ).values_list('course_id', flat=True))

        course_enrollments = CourseEnrollment.enrollments_for_user(user).filter(
            course_id__in=enterprise_enrollment_course_ids
        ).select_related('course')

        return list(course_enrollments)


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


class CourseRecommendationApiView(APIView):
    """
    **Example Request**

    GET api/dashboard/v0/recommendation/courses/
    """

    authentication_classes = (JwtAuthentication, SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """ Retrieves course recommendations details of a user in a specified course. """
        user_id = request.user.id
        is_control, course_keys = get_personalized_course_recommendations(user_id)

        # Emits an event to track student dashboard page visits.
        segment.track(
            user_id,
            'edx.bi.user.recommendations.viewed',
            {
                'is_personalized_recommendation': not is_control,
            }
        )

        if is_control or not course_keys:
            return Response(status=400)

        recommended_courses = []
        user_enrolled_course_keys = set()
        fields = ['title', 'owners', 'marketing_url']

        course_enrollments = CourseEnrollment.enrollments_for_user(request.user)
        for course_enrollment in course_enrollments:
            course_key = f'{course_enrollment.course_id.org}+{course_enrollment.course_id.course}'
            user_enrolled_course_keys.add(course_key)

        # Pick 5 course keys, excluding the user's already enrolled course(s).
        enrollable_course_keys = list(set(course_keys).difference(user_enrolled_course_keys))[:5]
        for course_id in enrollable_course_keys:
            course_data = get_course_data(course_id, fields)
            if course_data:
                recommended_courses.append({
                    'course_key': course_id,
                    'title': course_data['title'],
                    'logo_image_url': course_data['owners'][0]['logo_image_url'],
                    'marketing_url': course_data.get('marketing_url')
                })

        segment.track(user_id, 'edx.bi.user.recommendations.count', {'count': len(recommended_courses)})
        return Response({'courses': recommended_courses, 'is_personalized_recommendation': not is_control}, status=200)
