import json
import logging
import copy
from django.db.models import Q

from rest_framework import views, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import UsageKey, CourseKey

from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import Class
from openedx.features.genplus_features.genplus_assessments.models import UserResponse, UserRating
from openedx.features.genplus_features.genplus_learning.models import Unit
from openedx.features.genplus_features.genplus.api.v1.permissions import IsTeacher
from .serializers import ClassSerializer, TextAssessmentSerializer, RatingAssessmentSerializer
from openedx.features.genplus_features.genplus_assessments.constants import (
    TOTAL_PROBLEM_SCORE, INTRO_RATING_ASSESSMENT_RESPONSE,
    OUTRO_RATING_ASSESSMENT_RESPONSE, MAX_SKILLS_SCORE
)
from openedx.features.genplus_features.genplus_assessments.utils import (
    build_students_result, get_assessment_problem_data, get_assessment_completion
)


logger = logging.getLogger(__name__)


class ClassFilterApiView(views.APIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request, **kwargs):
        class_id = kwargs.get('class_id', None)
        try:
            gen_class = Class.objects.get(pk=class_id)
            gen_class_data = ClassSerializer(gen_class).data
        except Class.DoesNotExist:
            return Class.objects.none()
        return Response(gen_class_data)


class StudentAnswersViewSet(viewsets.ViewSet):
    """
    Comoute the analytics of student answers for a class

    Returns:
        Response: Returns a dictionaries
                containing the students analytics
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]

    def students_problem_response(self, request, **kwargs):
        class_id = kwargs.get('class_id', None)
        student_id = request.query_params.get('student_id')
        problem_id = request.query_params.get('problem_id')
        students = []
        response = {}
        try:
            if student_id == "all":
                gen_class = Class.objects.prefetch_related(
                    'students').get(pk=class_id)
                students = gen_class.students.exclude(gen_user__user__isnull=True)
                students = list(students.values_list('gen_user__user', flat=True))
            else:
                students.append(student_id)

            course_id = request.query_params.get('course_id')
            course_key = CourseKey.from_string(course_id)
            problem_locations = request.query_params.get('problem_locations')
            filter_type = request.query_params.get('filter')

            single_problem = False
            if student_id == "all" and filter_type == "individual_response":
                single_problem = True

            response = build_students_result(
                user_id=self.request.user.id,
                course_key=course_key,
                usage_key_str=problem_locations,
                student_list=students,
                filter_type=filter_type,
                problem_id=problem_id,
                single_problem=single_problem
            )
        except Exception as ex:
            logger.exception(ex)

        return Response(response)


class SkillAssessmentViewSet(viewsets.ViewSet):
    """
    Generate the skill assessment aggregate or individual result for a class or student

    Returns:
        Response: Returns a dictionaries
                containing the students aggregate or individual class base result data.
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    intro_assessments = None
    outro_assessments = None

    def aggregate_assessments_response(self, request, **kwargs):
        """
        Compute the aggregate result of all skill assessment problems for a class
        """
        class_id = kwargs.get('class_id')
        student_id = request.query_params.get('student_id')
        response = {
            'aggregate_all_problem': {},
            'aggregate_skill': {},
            'single_assessment_result': {}
        }

        try:
            gen_class = Class.objects.get(pk=class_id)
            if student_id != "all" and student_id is not None:
                text_assessment = UserResponse.objects.filter(user=student_id, gen_class=class_id, program=gen_class.program)
                rating_assessment = UserRating.objects.filter(user=student_id, gen_class=class_id, program=gen_class.program)
            else:
                text_assessment = UserResponse.objects.filter(gen_class=class_id, program=gen_class.program)
                rating_assessment = UserRating.objects.filter( gen_class=class_id, program=gen_class.program)

            text_assessment_data = TextAssessmentSerializer(text_assessment, many=True).data
            rating_assessment_data = RatingAssessmentSerializer(rating_assessment, many=True).data
            raw_data = text_assessment_data + rating_assessment_data

            if student_id == "all" or student_id is None:
                response['aggregate_all_problem'] = self.get_aggregate_problems_result(raw_data, gen_class)
                response['single_assessment_result'] = self.get_assessment_result(raw_data, gen_class)
            else:
                response['single_assessment_result'] = self.get_user_assessment_result(raw_data, gen_class)

            response['aggregate_skill'] = self.get_aggregate_skill_result(raw_data, gen_class, student_id)
        except Exception as ex:
            logger.exception(ex)

        return Response(response)

    def single_assessment_response(self, request, **kwargs):
        """
        Generate the result of single skill assessment problem for a class
        """
        class_id = kwargs.get('class_id')
        start_year_usage_key = request.query_params.get(
            'start_year_usage_key', None)
        end_year_usage_key = request.query_params.get(
            'end_year_usage_key', None)
        assessment_type = request.query_params.get('assessment_type', None)
        response = {}
        store = modulestore()
        try:
            usage_key = UsageKey.from_string(start_year_usage_key)
            gen_class = Class.objects.get(pk=class_id)
            students = gen_class.students.exclude(gen_user__user__isnull=True)
            total_students = students.count()
            response = {
                'question_statement': store.get_item(usage_key).question_statement,
                'assessment_type': assessment_type,
                'total_respones': total_students * 2,
                'available_responses': 0,
                'student_response': {}
            }

            if assessment_type == "genz_text_assessment":
                text_assessment = UserResponse.objects.filter(Q(program=gen_class.program) & Q(
                    gen_class=class_id) & (Q(usage_id=start_year_usage_key) | Q(usage_id=end_year_usage_key)))
                text_assessment_data = TextAssessmentSerializer(text_assessment, many=True).data
                raw_data = text_assessment_data
            else:
                rating_assessment = UserRating.objects.filter(Q(program=gen_class.program) & Q(
                    gen_class=class_id) & (Q(usage_id=start_year_usage_key) | Q(usage_id=end_year_usage_key)))
                rating_assessment_data = RatingAssessmentSerializer(rating_assessment, many=True).data
                raw_data = rating_assessment_data

            # prepare response against all the students in a class
            for student in students:
                user_id = 'user_' + str(student.gen_user.user_id)
                response['student_response'][user_id] = {
                    'full_name': student.gen_user.user.get_full_name(),
                    'score_start_of_year': 0,
                    'score_end_of_year': 0,
                    'total_score': TOTAL_PROBLEM_SCORE
                }
                if assessment_type == "genz_text_assessment":
                    response['student_response'][user_id]['response_start_of_year'] = None
                    response['student_response'][user_id]['response_end_of_year'] = None

            response.update(
                self.get_single_assessment_response(raw_data, response))
        except Exception as ex:
            logger.exception(ex)

        return Response(response)

    def get_aggregate_problems_result(self, raw_data, gen_class):
        """
        Generate aggregate result for assessment on base of class as per the user state  under the
        ``problem_location`` root.
        Arguments:
            raw_data (list): data get from UserResponse and UserRating models.
            gen_class (Class Model Object)
        Returns:
                [Dict]: Returns a dictionaries
                containing the students aggregate class base result data.
        """
        students = gen_class.students.exclude(gen_user__user__isnull=True)
        total_students = students.count()
        aggregate_result = {
            'total_students': total_students,
            'accumulative_all_problem_score': 0,
            'average_score_start_of_year': 0,
            'average_score_end_of_year': 0,
            'response_start_of_year': 0,
            'response_end_of_year': 0
        }
        # list of user id who complete all the assessment in the intro course
        intro_user = []
        # list of user id who complete all the assessment in the outro course
        outro_user = []

        for student in students:
            user = student.gen_user.user
            if gen_class.program.intro_unit:
                self.intro_assessments = get_assessment_problem_data(gen_class.program.intro_unit.id, user, self.request)
                intro_assessments_completion = get_assessment_completion(self.intro_assessments)
                if intro_assessments_completion:
                    intro_user.append(user.id)
                    aggregate_result['response_start_of_year'] += 1
            if gen_class.program.outro_unit:
                self.outro_assessments = get_assessment_problem_data(gen_class.program.outro_unit.id, user, self.request)
                outro_assessments_completion = get_assessment_completion(self.outro_assessments)
                if outro_assessments_completion:
                    outro_user.append(user.id)
                    aggregate_result['response_end_of_year'] += 1

        for data in raw_data:
            if data['assessment_time'] == "start_of_year" and data['user'] in intro_user:
                aggregate_result['average_score_start_of_year'] += data['score'] if 'score' in data else data['rating']
            elif data['assessment_time'] == "end_of_year" and data['user'] in outro_user:
                aggregate_result['average_score_end_of_year'] += data['score'] if 'score' in data else data['rating']

        total_problems = len(self.intro_assessments)
        aggregate_result['average_score_start_of_year'] /= aggregate_result['response_start_of_year'] if aggregate_result['response_start_of_year'] > 0 else 1
        aggregate_result['average_score_end_of_year'] /= aggregate_result['response_end_of_year'] if aggregate_result['response_end_of_year'] > 0 else 1
        aggregate_result['accumulative_all_problem_score'] = total_problems * TOTAL_PROBLEM_SCORE

        return aggregate_result

    def get_aggregate_skill_result(self, raw_data, gen_class, student_id):
        """
        Generate aggregate result for assessment for web chart on base of
        skills as per the user state  under the
        ``problem_location`` root.
        Arguments:
            raw_data (list): data get from UserResponse and UserRating models.
        Returns:
                [Dict]: Returns a dictionaries
                containing the students aggregate skill base result data.
        """
        aggregate_result = {}
        response = {}
        units = Unit.objects.filter(program=gen_class.program)
        # student who attempts start of year skill assessment problem
        intro_user = set()
        # student who attempts end of year skill assessment problem
        outro_user = set()
        for unit in units:
            if unit.skill:
                aggregate_result[unit.skill.name] = {
                        'skill': unit.skill.name,
                        'score_start_of_year': 0,
                        'score_end_of_year': 0,
                        'max_skills_score': MAX_SKILLS_SCORE
                    }
                response[unit.skill.name] = {
                    'response_start_of_year': 0,
                    'response_end_of_year': 0
                }

        for data in raw_data:
            if data['assessment_time'] == "start_of_year":
                aggregate_result[data['skill']
                                    ]['score_start_of_year'] += data['score'] if 'score' in data else data['rating']
                intro_user.add(data['user'])
            else:
                aggregate_result[data['skill']
                                    ]['score_end_of_year'] += data['score'] if 'score' in data else data['rating']
                outro_user.add(data['user'])

        response_start_of_year = len(intro_user)
        response_end_of_year = len(outro_user)

        if student_id == 'all' or student_id is None:
            for key,_ in aggregate_result.items():
                if response_start_of_year > 0:
                    aggregate_result[key]['score_start_of_year'] /= response_start_of_year
                if response_end_of_year > 0:
                    aggregate_result[key]['score_end_of_year'] /= response_end_of_year

        return aggregate_result

    def get_assessment_result(self, raw_data, gen_class):
        """
        Generate aggregate result for single assessment for bar and graph char on base of single assessment
        as per the user state  under the ``problem_location`` root.
        Arguments:
            raw_data (list): data get from UserResponse and UserRating models.
        Returns:
                [Dict]: Returns a dictionaries
                containing the students aggregate result for single assessment.
        """
        user = self.request.user
        total_students = gen_class.students.exclude(gen_user__user__isnull=True).count()
        store = modulestore()
        assessments = []
        aggregate_result = {}

        # get assessment usage key and type for program intro assessment course
        if self.intro_assessments is None:
            if gen_class.program.intro_unit:
                assessments.extend(get_assessment_problem_data(gen_class.program.intro_unit.id, user, self.request))
        else:
            assessments.extend(self.intro_assessments)

        # get assessment usage key and type for program outro assessment course
        if self.outro_assessments is None:
            if gen_class.program.outro_unit:
                assessments.extend(get_assessment_problem_data(gen_class.program.outro_unit.id, user, self.request))
        else:
            assessments.extend(self.outro_assessments)

        # prepare dictionary for every particular assessment problem in a course
        for assessment in assessments:
            usage_key = UsageKey.from_string(assessment.get('id'))
            assessment_xblock = store.get_item(usage_key)
            problem_id = str(assessment_xblock.problem_id)
            if problem_id not in aggregate_result:
                aggregate_result[problem_id] = {
                    'problem_statement': assessment_xblock.question_statement,
                    'assessment_type': assessment.get('type'),
                    'total_respones': total_students * 2,
                    'skill': assessment_xblock.select_assessment_skill,
                    'total_problem_score': TOTAL_PROBLEM_SCORE,
                    'count_response_start_of_year': 0,
                    'count_response_end_of_year': 0
                }
                if assessment.get('type') == 'genz_rating_assessment':
                    aggregate_result[problem_id]['rating_start_of_year'] = copy.deepcopy(
                        INTRO_RATING_ASSESSMENT_RESPONSE)
                    aggregate_result[problem_id]['rating_end_of_year'] = copy.deepcopy(
                        OUTRO_RATING_ASSESSMENT_RESPONSE)
                else:
                    aggregate_result[problem_id]['score_start_of_year'] = 0
                    aggregate_result[problem_id]['score_end_of_year'] = 0
                if assessment_xblock.select_assessment_time == "start_of_year":
                    aggregate_result[problem_id]['usage_key_start_of_year'] = assessment.get('id')
                else:
                    aggregate_result[problem_id]['usage_key_end_of_year'] = assessment.get('id')
            else:
                if assessment_xblock.select_assessment_time == "start_of_year":
                    aggregate_result[problem_id]['usage_key_start_of_year'] = assessment.get('id')
                else:
                    aggregate_result[problem_id]['usage_key_end_of_year'] = assessment.get('id')

        for data in raw_data:
            problem_id = data['problem_id']
            if data['assessment_time'] == "start_of_year":
                aggregate_result[problem_id]['count_response_start_of_year'] += 1
                if 'score' in data:
                    aggregate_result[problem_id]['score_start_of_year'] += data['score']
                else:
                    aggregate_result[problem_id]['rating_start_of_year'][str(data['rating'])] += 1
            else:
                aggregate_result[problem_id]['count_response_end_of_year'] += 1
                if 'score' in data:
                    aggregate_result[problem_id]['score_end_of_year'] += data['score']
                else:
                    aggregate_result[problem_id]['rating_end_of_year'][str(data['rating'])] += 1

        return aggregate_result

    def get_single_assessment_response(self, raw_data, response):
        """
        update response for single assessment for every student in a class under the
        ``problem_location`` root.
        Arguments:
            raw_data (list): data get from UserResponse OR UserRating models.
            response(dict):
        Returns:
                [Dict]: Returns a dictionaries
                containing the students updated response.
        """
        for data in raw_data:
            user_id = 'user_' + str(data['user'])
            if data['assessment_time'] == "start_of_year":
                response['available_responses'] += 1
                if 'student_response' in data:
                    response['student_response'][user_id]['response_start_of_year'] = json.loads(
                        data['student_response'])
                    response['student_response'][user_id]['score_start_of_year'] = data['score']
                else:
                    response['student_response'][user_id]['score_start_of_year'] = data['rating']
            else:
                response['available_responses'] += 1
                if 'student_response' in data:
                    response['student_response'][user_id]['response_end_of_year'] = json.loads(
                        data['student_response'])
                    response['student_response'][user_id]['score_end_of_year'] = data['score']
                else:
                    response['student_response'][user_id]['score_end_of_year'] = data['rating']

        return response

    def get_user_assessment_result(self, raw_data, gen_class):
        """
        Generate result for single user for bar and graph char on base of single assessment
        as per the user state  under the ``problem_location`` root.
        Arguments:
            raw_data (list): data get from UserResponse and UserRating models.
        Returns:
                [Dict]: Returns a dictionaries
                containing a student result for all single assessment.
        """
        store = modulestore()
        assessments = []
        aggregate_result = {}
        user = self.request.user

        # get assessment usage key and type for program intro assessment course
        if self.intro_assessments is None:
            if gen_class.program.intro_unit:
                assessments.extend(get_assessment_problem_data(gen_class.program.intro_unit.id, user, self.request))
        else:
            assessments.extend(self.intro_assessments)

        # get assessment usage key and type for program outro assessment course
        if self.outro_assessments is None:
            if gen_class.program.outro_unit:
                assessments.extend(get_assessment_problem_data(gen_class.program.outro_unit.id, user, self.request))
        else:
            assessments.extend(self.outro_assessments)

        # prepare dictionary for every particular assessment problem in a course
        for assessment in assessments:
            usage_key = UsageKey.from_string(assessment.get('id'))
            assessment_xblock = store.get_item(usage_key)
            problem_id = str(assessment_xblock.problem_id)
            if problem_id not in aggregate_result:
                aggregate_result[problem_id] = {
                    'problem_statement': assessment_xblock.question_statement,
                    'assessment_type': assessment.get('type'),
                    'skill': assessment_xblock.select_assessment_skill,
                    'total_problem_score': TOTAL_PROBLEM_SCORE,
                    'score_start_of_year': 0,
                    'score_end_of_year': 0,
                }
                if assessment.get('type') == 'genz_text_assessment':
                    aggregate_result[problem_id]['response_start_of_year'] = None
                    aggregate_result[problem_id]['response_end_of_year'] = None

        for data in raw_data:
            problem_id = data['problem_id']
            if data['assessment_time'] == "start_of_year":
                if 'score' in data:
                    aggregate_result[problem_id]['response_start_of_year'] = json.loads(
                        data['student_response'])
                    aggregate_result[problem_id]['score_start_of_year'] = data['score']
                else:
                    aggregate_result[problem_id]['score_start_of_year'] = data['rating']
            else:
                if 'score' in data:
                    aggregate_result[problem_id]['response_end_of_year'] = json.loads(
                        data['student_response'])
                    aggregate_result[problem_id]['score_end_of_year'] = data['score']
                else:
                    aggregate_result[problem_id]['score_end_of_year'] = data['rating']

        return aggregate_result
