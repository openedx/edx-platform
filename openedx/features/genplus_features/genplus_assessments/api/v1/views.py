import json
import logging
from django.db.models import Q

from rest_framework import views, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import UsageKey, CourseKey

from openedx.features.course_experience.utils import get_course_outline_block_tree
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus.models import Class
from openedx.features.genplus_features.genplus_assessments.models import UserResponse, UserRating
from openedx.features.genplus_features.genplus.api.v1.permissions import IsTeacher
from .serializers import ClassSerializer, TextAssessmentSerializer, RatingAssessmentSerializer
from openedx.features.genplus_features.genplus_assessments.constants import TOTAL_PROBLEM_SCORE, INTRO_RATING_ASSESSMENT_RESPONSE ,OUTRO_RATING_ASSESSMENT_RESPONSE
from openedx.features.genplus_features.genplus_assessments.utils import (
    build_students_result,
)

logger = logging.getLogger(__name__)


class ClassFilterViewSet(views.APIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ClassSerializer

    def get(self,request, **kwargs):
        class_id = kwargs.get('class_id', None)
        try:
            gen_class = Class.objects.get(pk=class_id)
            gen_class_data = ClassSerializer(gen_class).data
        except Class.DoesNotExist:
            return Class.objects.none()
        return Response(gen_class_data)

class StudentAnswersView(viewsets.ViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]

    def students_problem_response(self, request, **kwargs):
        class_id = kwargs.get('class_id', None)
        student_id = request.query_params.get('student_id',None)
        students = []
        try:
            if student_id == "all":
                students = list(Class.objects.prefetch_related('students').get(pk=class_id).students.values_list('gen_user__user_id',flat=True))
            else:
                students.append(student_id)
            course_id = request.query_params.get('course_id',None)
            course_key = CourseKey.from_string(course_id)
            problem_locations = request.query_params.get('problem_locations',None)
            filter_type = request.query_params.get('filter',None)

            response = build_students_result(
                user_id=self.request.user.id,
                course_key=course_key,
                usage_key_str=problem_locations,
                student_list=students,
                filter_type=filter_type,
            )
        except Exception as e:
                logger.exception(e)

        return Response(response)

class SkillAssessmentView(viewsets.ViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]

    def aggregate_assessments_response(self, request, **kwargs):
        class_id = kwargs.get('class_id')
        student_id = request.query_params.get('student_id',None)
        response = dict()
        response['aggregate_all_problem'] = dict()
        response['aggregate_skill'] = dict()
        response['single_assessment_result'] = dict()
        try:
            gen_class = Class.objects.get(pk=class_id)
            if student_id != "all" and student_id is not None:
                text_assessment = UserResponse.objects.filter(user=student_id, gen_class=class_id, program=gen_class.program)
                rating_assessment = UserRating.objects.filter(user=student_id, gen_class=class_id, program=gen_class.program)
            else:
                text_assessment = UserResponse.objects.filter(gen_class=class_id, program=gen_class.program)
                rating_assessment = UserRating.objects.filter(gen_class=class_id, program=gen_class.program)
            text_assessment_data = TextAssessmentSerializer(text_assessment, many=True).data
            rating_assessment_data = RatingAssessmentSerializer(rating_assessment, many=True).data
            raw_data = text_assessment_data + rating_assessment_data
            response['aggregate_all_problem'] = self.get_aggregate_problems_result(raw_data, gen_class)
            response['aggregate_skill'] = self.get_aggregate_skill_result(raw_data)
            if student_id == "all":
                response['single_assessment_result'] = self.get_assessment_result(raw_data, gen_class)
            else:
                response['single_assessment_result'] = self.get_user_assessment_result(raw_data, gen_class)
        except Exception as e:
                logger.exception(e)

        return Response(response)

    
    def single_assessment_response(self, request, **kwargs):
        class_id = kwargs.get('class_id')
        start_year_usage_key = request.query_params.get('start_year_usage_key',None)
        end_year_usage_key = request.query_params.get('end_year_usage_key',None)
        assessment_type = request.query_params.get('assessment_type',None)
        response = dict()
        store = modulestore()
        try:
            usage_key = UsageKey.from_string(start_year_usage_key)
            gen_class = Class.objects.get(pk=class_id)
            response['question_statement'] = store.get_item(usage_key).question_statement
            response['assessment_type'] = assessment_type
            response['total_respones'] = gen_class.students.count() * 2
            response['available_responses'] = 0
            response['student_response'] = dict()
            if assessment_type == "genz_text_assessment":
                text_assessment = UserResponse.objects.filter(Q(program=gen_class.program) & Q(gen_class=class_id) & (Q(usage_id=start_year_usage_key) | Q(usage_id=end_year_usage_key)))
                text_assessment_data = TextAssessmentSerializer(text_assessment, many=True).data
                raw_data = text_assessment_data
            else:
                rating_assessment = UserRating.objects.filter(Q(program=gen_class.program) & Q(gen_class=class_id) & (Q(usage_id=start_year_usage_key) | Q(usage_id=end_year_usage_key)))
                rating_assessment_data = RatingAssessmentSerializer(rating_assessment, many=True).data
                raw_data = rating_assessment_data

            students = gen_class.students.all()
            #prepare response against all the students in a class
            for student in students:
                user_id = 'user_' + str(student.gen_user.user_id)
                response['student_response'][user_id] = dict()
                response['student_response'][user_id]['full_name'] = student.gen_user.user.get_full_name()
                response['student_response'][user_id]['score_start_of_year'] = 0
                response['student_response'][user_id]['score_end_of_year'] = 0
                response['student_response'][user_id]['total_score'] = TOTAL_PROBLEM_SCORE
                if assessment_type == "genz_text_assessment":
                    response['student_response'][user_id]['response_start_of_year'] = None
                    response['student_response'][user_id]['response_end_of_year'] = None

            response.update(self.get_single_assessment_response(raw_data, response))
        except Exception as e:
           logger.exception(e)

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
        problem_ids = dict()
        aggregate_result = dict()
        aggregate_result['total_students'] = gen_class.students.count()
        aggregate_result['accumulative_all_problem_score'] = 0
        aggregate_result['accumulative_score_start_of_year'] = 0
        aggregate_result['accumulative_score_end_of_year'] = 0
        aggregate_result['count_response_start_of_year'] = 0
        aggregate_result['count_response_end_of_year'] = 0
        for data in raw_data:
            if data['problem_id'] not in problem_ids:
                problem_ids[data['problem_id']] = dict()
                problem_ids[data['problem_id']]['count_response_start_of_year'] = 0
                problem_ids[data['problem_id']]['count_response_end_of_year'] = 0
                if data['assessment_time'] == "start_of_year":
                    problem_ids[data['problem_id']]['count_response_start_of_year'] += 1
                    aggregate_result['accumulative_all_problem_score'] += TOTAL_PROBLEM_SCORE
                    aggregate_result['accumulative_score_start_of_year'] += data['score'] if 'score' in data else data['rating']
                else:
                    problem_ids[data['problem_id']]['count_response_end_of_year'] += 1
                    aggregate_result['accumulative_score_end_of_year'] += data['score'] if 'score' in data else data['rating']
            else:
                if data['assessment_time'] == "start_of_year":
                    problem_ids[data['problem_id']]['count_response_start_of_year'] += 1
                    aggregate_result['accumulative_score_start_of_year'] += data['score'] if 'score' in data else data['rating']
                else:
                    problem_ids[data['problem_id']]['count_response_end_of_year'] += 1
                    aggregate_result['accumulative_score_end_of_year'] += data['score'] if 'score' in data else data['rating']
        
        aggregate_result['count_response_start_of_year'] = problem_ids[next(iter(problem_ids))]['count_response_start_of_year'] if len(problem_ids) > 0 else 0
        aggregate_result['count_response_end_of_year'] = problem_ids[next(iter(problem_ids))]['count_response_end_of_year'] if len(problem_ids) > 0 else 0

        return aggregate_result

    def get_aggregate_skill_result(self, raw_data):
        """
        Generate aggregate result for assessment for web chart on base of skills as per the user state  under the
        ``problem_location`` root.
        Arguments:
            raw_data (list): data get from UserResponse and UserRating models.
        Returns:
                [Dict]: Returns a dictionaries
                containing the students aggregate skill base result data.
        """
        aggregate_result =  dict()
        for data in raw_data:
            data = dict(data)
            if data['skill'] not in aggregate_result:
                aggregate_result[data['skill']] = dict()
                aggregate_result[data['skill']]['skill'] = data['skill']
                aggregate_result[data['skill']]['score_start_of_year'] = 0
                aggregate_result[data['skill']]['score_end_of_year'] = 0
                if data['assessment_time'] == "start_of_year":
                    aggregate_result[data['skill']]['score_start_of_year'] += data['score'] if 'score' in data else data['rating']
                else:
                    aggregate_result[data['skill']]['score_end_of_year'] += data['score'] if 'score' in data else data['rating']
            else:
                if data['assessment_time'] == "start_of_year":
                    aggregate_result[data['skill']]['score_start_of_year'] += data['score'] if 'score' in data else data['rating']
                else:
                    aggregate_result[data['skill']]['score_end_of_year'] += data['score'] if 'score' in data else data['rating']

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
        store = modulestore()
        assessments = []
        aggregate_result =  dict()
        #get assessment usage key and type for program intro assessment course
        assessments = self.get_assessment_block_data(gen_class.program.intro_unit.id)
        #get assessment usage key and type for program outro assessment course
        assessments.extend(self.get_assessment_block_data(gen_class.program.outro_unit.id))

        #prepare dictionary for every particular assessment problem in a course
        for assessment in assessments:
            usage_key = UsageKey.from_string(assessment.get('id'))
            assessment_xblock = store.get_item(usage_key)
            problem_id = str(assessment_xblock.problem_id)
            if problem_id not in aggregate_result:
                aggregate_result[problem_id] = dict()
                aggregate_result[problem_id]['problem_statement'] = assessment_xblock.question_statement
                aggregate_result[problem_id]['assessment_type'] = assessment.get('type')
                aggregate_result[problem_id]['total_respones'] = gen_class.students.count() * 2
                aggregate_result[problem_id]['skill'] = assessment_xblock.select_assessment_skill
                aggregate_result[problem_id]['total_problem_score'] = TOTAL_PROBLEM_SCORE
                aggregate_result[problem_id]['count_response_start_of_year'] = 0
                aggregate_result[problem_id]['count_response_end_of_year'] = 0
                if assessment.get('type') == 'genz_rating_assessment':
                    aggregate_result[problem_id]['rating_start_of_year'] = INTRO_RATING_ASSESSMENT_RESPONSE
                    aggregate_result[problem_id]['rating_end_of_year'] = OUTRO_RATING_ASSESSMENT_RESPONSE
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
                    response['student_response'][user_id]['response_start_of_year'] = json.loads(data['student_response'])
                    response['student_response'][user_id]['score_start_of_year'] = data['score']
                else:
                    response['student_response'][user_id]['score_start_of_year'] = data['rating']
            else:
                response['available_responses'] += 1
                if 'student_response' in data:
                    response['student_response'][user_id]['response_end_of_year'] = json.loads(data['student_response'])
                    response['student_response'][user_id]['score_end_of_year'] = data['score']
                else:
                    response['student_response'][user_id]['score_end_of_year'] = data['rating']

        return response

    def get_assessment_block_data(self, course_key):
        course_outline_blocks = get_course_outline_block_tree(self.request, str(course_key), self.request.user)
        if not course_outline_blocks:
            return []
        else:
            course_blocks_children = course_outline_blocks.get('children')
        assessments = self.get_assessment_course_block(
            course_blocks_children,
        )

        return assessments

    def get_assessment_course_block(self, course_blocks_children):
        """
        return assessment xblock usage key and type of that assessment xblock with in a.
        Arguments:
            course_blocks_children (list[dict]): course block data in form of tree
        Returns:
                list[Dict]: Returns a list of dictionaries
        """
        assessments = []
        for course_block in course_blocks_children:
            course_block_type = course_block.get('type')
            if course_block_type in ['genz_text_assessment','genz_rating_assessment']:
                return [{
                    'id':course_block.get('id'),
                    'type':course_block_type
                }]
            else:
                children = course_block.get('children')
                if children:
                    assessments.extend(self.get_assessment_course_block(children))
        return assessments
        
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
        aggregate_result =  dict()
        #get assessment usage key and type for program intro assessment course
        assessments = self.get_assessment_block_data(gen_class.program.intro_unit.id)
        #get assessment usage key and type for program outro assessment course
        assessments.extend(self.get_assessment_block_data(gen_class.program.outro_unit.id))

        #prepare dictionary for every particular assessment problem in a course
        for assessment in assessments:
            usage_key = UsageKey.from_string(assessment.get('id'))
            assessment_xblock = store.get_item(usage_key)
            problem_id = str(assessment_xblock.problem_id)
            if problem_id not in aggregate_result:
                aggregate_result[problem_id] = dict()
                aggregate_result[problem_id]['problem_statement'] = assessment_xblock.question_statement
                aggregate_result[problem_id]['assessment_type'] = assessment.get('type')
                aggregate_result[problem_id]['skill'] = assessment_xblock.select_assessment_skill
                aggregate_result[problem_id]['total_problem_score'] = TOTAL_PROBLEM_SCORE
                aggregate_result[problem_id]['score_start_of_year'] = 0
                aggregate_result[problem_id]['score_end_of_year'] = 0
                if assessment.get('type') == 'genz_text_assessment':
                    aggregate_result[problem_id]['response_start_of_year'] = None
                    aggregate_result[problem_id]['response_end_of_year'] = None

        for data in raw_data:
            problem_id = data['problem_id']
            if data['assessment_time'] == "start_of_year":
                if 'score' in data:
                    aggregate_result[problem_id]['response_start_of_year'] = json.loads(data['student_response'])
                    aggregate_result[problem_id]['score_start_of_year'] = data['score']
                else:
                    aggregate_result[problem_id]['score_start_of_year'] = data['rating']
            else:
                if 'score' in data:
                    aggregate_result[problem_id]['response_end_of_year'] = json.loads(data['student_response'])
                    aggregate_result[problem_id]['score_end_of_year'] = data['score']
                else:
                    aggregate_result[problem_id]['score_end_of_year'] = data['rating']

        return aggregate_result