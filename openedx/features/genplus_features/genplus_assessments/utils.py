import itertools
import json
from lxml import etree
from django.test import RequestFactory
from django.db.models import Q
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import UsageKey, CourseKey
from collections import defaultdict

from django.contrib.auth import get_user_model
from openedx.features.course_experience.utils import get_course_outline_block_tree
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.courseware.user_state_client import DjangoXBlockUserStateClient
from lms.djangoapps.courseware.models import StudentModule
from openedx.features.genplus_features.genplus.constants import JournalTypes
from openedx.features.genplus_features.genplus.models import Student, JournalPost
from openedx.features.genplus_features.genplus_learning.models import Unit
from openedx.features.genplus_features.genplus_assessments.constants import ProblemTypes, ProblemSetting, JOURNAL_STYLE, \
    TOTAL_PROBLEM_SCORE, SkillAssessmentTypes, SkillAssessmentResponseTime
from openedx.features.genplus_features.genplus_assessments.models import SkillAssessmentQuestion, \
    SkillAssessmentResponse


class StudentResponse:

    def __init__(self):
        self.problem_function_map = {
            ProblemSetting.IS_JOURNAL_ENTRY: self.create_and_update_journal_post_from_lms,
            ProblemSetting.IS_SKILL_ASSESSMENT: self.create_assessment_response_from_lms,
        }
        self.problem_setting_map = {
            ProblemSetting.IS_JOURNAL_ENTRY: ProblemTypes.JOURNAL_PROBLEMS,
            ProblemSetting.IS_SKILL_ASSESSMENT: ProblemTypes.SKILL_ASSESSMENT_PROBLEMS,
        }

    def save_problem_response(self, problem_block, student_response, event_info):
        user_id = getattr(problem_block.scope_ids, 'user_id')
        block_type = getattr(problem_block.scope_ids, 'block_type')
        if not (block_type and block_type == 'problem') or not user_id:
            return

        student = Student.objects.filter(gen_user__user=user_id).first()
        if not student:
            return

        parser = etree.XMLParser(remove_blank_text=True)
        problem_xml = etree.XML(problem_block.data, parser=parser)

        if problem_xml.tag == 'problem':
            problem_element = problem_xml
        else:
            problem_element = problem_xml.find('.//problem')

        if problem_element is not None:
            problem_classes = problem_element.get('class', '').split()
            if not problem_classes:
                return

        problem_type = problem_classes[0]

        for problem_attr, problem_function in self.problem_function_map.items():
            if(getattr(problem_block, problem_attr) == True and problem_type in self.problem_setting_map.get(problem_attr)):
                problem_function(**{
                    'student': student,
                    'problem_type': problem_type,
                    'problem_block': problem_block,
                    'event_info': event_info,
                    'student_response': student_response,
                    'problem_element': problem_element
                })

    def create_and_update_journal_post_from_lms(self, **kwargs):
        problem_block = kwargs.get('problem_block')
        problem_type = kwargs.get('problem_type')
        usage_id = problem_block.scope_ids.usage_id
        try:
            student_module = StudentModule.objects.get(
                student=kwargs.get('student').user,
                course_id=usage_id.course_key,
                module_state_key=usage_id,
            )

        except StudentModule.DoesNotExist:
            student_module = None
            print(f"===============Student module not found===================")

        if problem_type == ProblemTypes.SHORT_ANSWER:
            self._create_and_update_text_journal_entry(student_module=student_module, **kwargs)
        elif problem_type in ProblemTypes.CHOICE_TYPE_PROBLEMS:
            self._create_and_update_choice_journal_entry(student_module=student_module, **kwargs)

    def _get_course_skill(self, problem_block):
        course_key = problem_block.scope_ids.usage_id.course_key
        unit = Unit.objects.filter(course__id=course_key).first()
        return unit.skill if unit else None

    def _create_and_update_text_journal_entry(self, **kwargs):
        problem_block = kwargs.get('problem_block')
        parser = etree.XMLParser(remove_blank_text=True)
        problem = etree.XML(problem_block.get_problem_html(encapsulate=True), parser=parser)

        student_module = kwargs.get('student_module')
        for key, value in kwargs.get('student_response').items():
            if not value:
                continue
            uuid = key.replace('input_', '')
            title = self.extract_title(problem, key)
            if title:
                answer = json.loads(JOURNAL_STYLE.format(value), strict=False)
                defaults = {
                    'skill': self._get_course_skill(problem_block),
                    'journal_type': JournalTypes.STUDENT_POST,
                    'is_editable': False,
                    'title': title,
                    'description': json.dumps(answer),
                }
                if student_module:
                    defaults['created'] = student_module.created
                    defaults['modified'] = student_module.modified

                obj, created = JournalPost.objects.update_or_create(
                    uuid=uuid,
                    student=kwargs.get('student'),
                    defaults=defaults
                )

    @staticmethod
    def extract_title(problem, key):
        title_queries = [
            f".//label[@for='{key}']",
            ".//span[@class='question-text']",
            ".//label[@class='question-text']"
        ]

        for query in title_queries:
            title_element = problem.find(query)
            if title_element is not None and getattr(title_element, 'text'):
                return title_element.text

        return None

    def _create_and_update_choice_journal_entry(self, **kwargs):
        problem_block = kwargs.get('problem_block')
        parser = etree.XMLParser(remove_blank_text=True)
        problem = etree.XML(problem_block.data, parser=parser)

        student_module = kwargs.get('student_module')
        title = problem.find(".//*[@class='question-text']").text
        answer = self._aggregate_student_answer(**kwargs)
        defaults = {
            'skill': self._get_course_skill(problem_block),
            'journal_type': JournalTypes.PROBLEM_ENTRY,
            'is_editable': False,
            'title': title,
            'description': json.dumps(answer),
        }
        if student_module:
            defaults['created'] = student_module.created
            defaults['modified'] = student_module.modified

        obj, created = JournalPost.objects.update_or_create(
            uuid=answer['key'],
            student=kwargs.get('student'),
            defaults=defaults
        )

    def _aggregate_student_answer(self, **kwargs):
        event_info = kwargs.get('event_info')
        problem_xml = kwargs.get('problem_element')
        key, answers = next(iter(event_info['real_answers'].items()))
        total = len(event_info['real_answers'][key])
        correct = sum(answer in event_info['answers'][key] for answer in answers)
        aggregate_result = {
            'answers': [{'name': problem_xml.find(f".//choice[@class='{answer}']").text,
                         'value': answer in event_info['answers'][key]} for answer in answers]
        }
        return {
            'results': aggregate_result,
            'correct': correct,
            'total': total,
            'key': key
        }

    def create_assessment_response_from_lms(self, **kwargs):
        """
        Function to create a SkillAssessmentResponse instance from a given problem block and student response.

        Args:
            self: The instance of the calling class.
            problem_block (Block): The problem block which the student has responded to.
            student_response (str): The response submitted by the student.
            assessment_type (str): Type of Skill Assessment

        This function starts by extracting relevant data from the problem block, including the course key, problem key,
        and the HTML content of the problem. It parses the HTML content to extract the question text and choice options.

        It then tries to retrieve a SkillAssessmentQuestion instance that matches either the start unit or end unit
        of the problem block.

        If such a SkillAssessmentQuestion is found, the function then determines whether to set the response time to
        SkillAssessmentResponseTime.START_OF_YEAR or SkillAssessmentResponseTime.END_OF_YEAR, based on whether the
        problem key matches the start unit location or the end unit location.

        Finally, it creates a SkillAssessmentResponse instance, setting the user to the student, the question to the
        retrieved SkillAssessmentQuestion, the earned score based on the correctness of the student's response, the total
        score to a problem weight value, the response time as determined earlier, and the question data to the
        parsed problem block data. It then saves the created SkillAssessmentResponse instance to the database.
        """
        user_response = kwargs.get('student_response')
        problem_block = kwargs.get('problem_block')
        problem_type = kwargs.get('problem_type')
        user_id = getattr(problem_block.scope_ids, 'user_id')
        user = get_user_model().objects.get(pk=user_id)
        course_key = problem_block.scope_ids.usage_id.course_key
        problem_key = problem_block.scope_ids.usage_id
        total_score = problem_block.weight if problem_block.weight else 0

        problem_html = problem_block.data
        # Parse the HTML
        _, question_text, choices = self.extract_question_choices(problem_html)

        # Combine the question and choices into a single dictionary
        question_responses_dict = {'question': question_text, 'choices': choices}

        # Initialize an empty list to store response
        student_response = {}

        # Iterate over items in the MultiDict
        for _, value in user_response.items():
            # Each 'value' corresponds to a choice like 'choice_0'

            # Get corresponding choice text and point
            response_text = question_responses_dict['choices'][value]['text']
            response_point = question_responses_dict['choices'][value]['points']

            # Store this information in the student_responses list
            student_response = {
                'response_value': value,
                'response_text': response_text,
                'points': response_point
            }

            # only need to process one response, break the loop after the first iteration
            break

        # Update the dictionary with the student's response
        question_responses_dict['student_response'] = student_response
        earned_score = self._calculate_earned_score(question_responses_dict, total_score)
        response_time, question = self._get_assessment_time(course_key, problem_key)

        if problem_type == SkillAssessmentTypes.LIKERT:
            skill_assessment_type = SkillAssessmentTypes.LIKERT

        # update and create SkillAssessmentResponse object
        if response_time and question:
            SkillAssessmentResponse.objects.update_or_create(
                user=user,
                question=question,
                response_time=response_time,
                problem_location=problem_key,
                defaults={
                    'earned_score': earned_score,
                    'total_score': total_score,
                    'skill_assessment_type': skill_assessment_type,
                    'question_response': question_responses_dict,
                }
            )

    def _get_assessment_time(self, course_key, problem_key):
        try:
            # Fetch SkillAssessmentQuestion based on provided course_key and problem_key
            question = SkillAssessmentQuestion.objects.get(
                (Q(start_unit=course_key) & Q(start_unit_location=problem_key)) |
                (Q(end_unit=course_key) & Q(end_unit_location=problem_key))
            )
        except SkillAssessmentQuestion.DoesNotExist:
            # Handle case when the SkillAssessmentQuestion does not exist
            print("SkillAssessmentQuestion does not exist with the provided keys")
            return None, None

        if question.start_unit == course_key and question.start_unit_location == problem_key:
            return SkillAssessmentResponseTime.START_OF_YEAR, question

        return SkillAssessmentResponseTime.END_OF_YEAR, question

    def extract_question_choices(self, problem_html):
        # Parse the HTML
        parser = etree.XMLParser(recover=True)
        problem_xml = etree.fromstring(problem_html, parser=parser)

        # Extract the problem type
        problem_type = problem_xml.find('.//problem').attrib.get('class')

        # Extract the question
        question_text = problem_xml.find('.//*[@class="question-text"]').text

        # Extract the choices, whether they are correct, and the points associated
        choices = {
            choice.attrib['class']: {
                'text': choice.text,
                'points': int(choice.attrib['point'])
            }
            for choice in problem_xml.xpath('.//choice')
        }

        return problem_type, question_text, choices

    def _calculate_earned_score(self, question_responses_dict, total_score):
        """
        Calculates the score a student earned based on their responses to a question.

        Parameters:
        question_responses_dict (dict): A dictionary containing question, available
                                        choices, and the student's response. Each
                                        choice and response includes points indicating
                                        its score value.
        total_score (int): Max possible score for a problem

        Returns:
        score (int): The total score the student earned for the question.
        """
        # Get the points associated with the student's response
        points = question_responses_dict['student_response']['points']

        # Calculate the total number of choices available for this question
        total_choices = len(question_responses_dict['choices'].values())

        # Compute the base score per choice, assuming equal distribution of total score among all choices
        base_score = total_score / total_choices

        # Calculate the score as the product of base score and points associated with the student's response
        # Round the score to the nearest integer for simplicity
        score = round(base_score * points)

        return score


def build_problem_list(course_blocks, root, path=None):
    """
    Generate a tuple of display names, block location paths and block keys
    for all problem blocks under the ``root`` block.
    Arguments:
        course_blocks (BlockStructureBlockData): Block structure for a course.
        root (UsageKey): This block and its children will be used to generate
            the problem list
        path (List[str]): The list of display names for the parent of root block
    Yields:
        Tuple[str, List[str], UsageKey]: tuple of a block's display name, path, and
            usage key
    """
    name = course_blocks.get_xblock_field(
        root, 'display_name') or root.block_type
    if path is None:
        path = [name]

    yield name, path, root

    for block in course_blocks.get_children(root):
        name = course_blocks.get_xblock_field(
            block, 'display_name') or block.block_type
        yield from build_problem_list(course_blocks, block, path + [name])


def build_students_result(user_id, course_key, usage_key_str, student_list, filter_type, problem_id, single_problem):
    """
    Generate a result for problem responses for all problem under the
    ``problem_location`` root.
    Arguments:
        user_id (int): The user id for the user generating the report
        course_key (CourseKey): The ``CourseKey`` for the course whose report
            is being generated
        usage_key_str: The generated report will include these
            blocks and their child blocks.
        filter_type (str): The filter_type type tells us that response generate on individual basis or aggregate basis.
    Returns:
        List[Dict]: Returns a list of dictionaries
            containing the student aggregate result data.
    """
    from openedx.features.genplus_features.genplus_learning.utils import generate_report_data
    usage_key = UsageKey.from_string(usage_key_str).map_into_course(course_key)
    user = get_user_model().objects.get(pk=user_id)

    if single_problem:
        student_data = {}
    else:
        student_data = []

    store = modulestore()
    user_state_client = DjangoXBlockUserStateClient()

    with store.bulk_operations(course_key):
        course_blocks = get_course_blocks(user, usage_key)
        for _, _, block_key in build_problem_list(course_blocks, usage_key):
            # Chapter and sequential blocks are filtered out since they include state
            # which isn't useful for this report.
            if block_key.block_type in ('sequential', 'chapter'):
                continue

            block = store.get_item(block_key)
            generated_report_data = defaultdict(list)

            # Blocks can implement the generate_report_data method to provide their own
            # human-readable formatting for user state.
            if hasattr(block, 'generate_report_data'):
                try:
                    user_state_iterator = user_state_client.iter_all_for_block(
                        block_key, student_list=student_list)
                    for username, state in generate_report_data(block, user_state_iterator):
                        state['block_key'] = block_key
                        generated_report_data[username].append(state)
                except NotImplementedError:
                    pass

            responses = {}

            if block_key.block_type in ('problem'):
                responses = get_problem_attributes(block.data, block_key)
                aggregate_result = {}
                user_short_answers = {}
                if responses['problem_type'] in ProblemTypes.CHOICE_TYPE_PROBLEMS:
                    responses['results'] = []
                else:
                    responses['results'] = {}
                students_answered_count = 0
                for user_id in student_list:
                    user = get_user_model().objects.get(pk=user_id)
                    user_states = generated_report_data.get(user.username)
                    if user_states:
                        # increment in student answer count in case of user_states exists
                        students_answered_count += 1
                        # For each response in the block, aggregate the result for the problem, and add in the responses
                        if responses['problem_type'] in ProblemTypes.CHOICE_TYPE_PROBLEMS:
                            if filter_type == "aggregate_response":
                                aggregate_result.update(
                                    students_aggregate_result(
                                        user_states,
                                        aggregate_result,
                                        responses['problem_choices'],
                                    )
                                )
                            elif filter_type == "individual_response":
                                responses['results'].append(
                                    students_multiple_choice_response(user_states, user))
                        elif responses['problem_type'] == ProblemTypes.SHORT_ANSWER:
                            for user_state in user_states:
                                answer_id = problem_id if problem_id is not None else user_state['Answer ID']
                                if answer_id not in user_short_answers:
                                    user_short_answers[answer_id] = {
                                        'question_text': user_state['Question'],
                                        'answer_id': user_state['Answer ID'],
                                        'answers': [
                                            get_students_short_answer_response(user_state, user)] if answer_id ==
                                                                                                     user_state[
                                                                                                         'Answer ID'] else []
                                    }
                                else:
                                    if answer_id == user_state['Answer ID']:
                                        user_short_answers[answer_id]['answers'].append(
                                            get_students_short_answer_response(user_state, user))

                if responses['problem_type'] == ProblemTypes.SHORT_ANSWER and len(user_short_answers) > 0:
                    responses['results'].update(user_short_answers)

                if responses[
                    'problem_type'] in ProblemTypes.CHOICE_TYPE_PROBLEMS and filter_type == "aggregate_response":
                    for key, value in aggregate_result.items():
                        responses['results'].append({
                            'title': key,
                            'count': value['count'],
                            'is_correct': value['is_correct'],
                        })

                if responses['problem_type'] in ProblemTypes.STUDENT_ANSWER_PROBLEMS:
                    if not single_problem:
                        if not filter_type == "individual_response":
                            responses['students_count'] = len(student_list)
                            responses['students_answered_count'] = students_answered_count
                        student_data.append(responses)
                    else:
                        student_data.update(responses)

    return student_data


def students_aggregate_result(user_states, aggregate_result, problem_choices):
    """
    Generate aggregate response for problem(Multiple Choices and Single Choices) as per the user state  under the
    ``problem_location`` root.
    Arguments:
        user_State (List): The user id for the user generating the report

    Returns:
            [Dict]: Returns a dictionaries
            containing the students aggregate result data.
    """
    for key in problem_choices.keys():
        key = key.strip()
        choice = problem_choices[key]
        if choice['statement'] not in aggregate_result:
            statement=choice['statement'].strip()
            aggregate_result[statement] = {
                'count': 0,
                'is_correct': choice['correct'] == 'true'
            }

    for user_state in user_states:
        user_answer = user_state['Answer']
        correct_answer = user_state['Correct Answer']
        keys = user_answer.split('||')
        for k in keys:
            k = k.strip()
            if k not in aggregate_result:
                aggregate_result[k] = {
                    'count': 1,
                    'is_correct': k in correct_answer
                }
            else:
                aggregate_result[k]['count'] += 1

    return aggregate_result


def get_problem_attributes(raw_data, block_key):
    """
    Parse the problem which we got in the form of XML and extract
    the problem information(title of problem, problem text and choices)
    for a paricular problem under the
    ``problem_location`` root.
    Arguments:
        block_key: The block_key so that we get the problem data from mongo DB

    Returns:
            [Dict]: Returns a dictionaries
            containing the problem data.
    """
    responses = {
        'problem_key': str(block_key),
        'problem_id': block_key.block_id,
        'selection': 0
    }
    parser = etree.XMLParser(remove_blank_text=True)
    problem = etree.XML(raw_data, parser=parser)
    data_dict = {}
    for e in problem.iter("*"):
        if e.tag == 'problem':
            responses['problem_type'] = e.attrib.get('class')
        elif e.text and e.attrib.get('class') == 'question-text' and responses['problem_type'] != ProblemTypes.SHORT_ANSWER:
            responses['question_text'] = e.text
        elif e.text and e.tag == 'choice':
            choice_dict = {
                'statement': str(e.text).strip(),
                'correct': e.attrib.get('correct')
            }
            if e.attrib.get('correct') == 'true':
                responses['selection'] += 1
            data_dict.update({e.attrib.get('class'): choice_dict})
    if responses['problem_type'] != ProblemTypes.SHORT_ANSWER:
        responses['problem_choices'] = data_dict
    return responses


def get_students_short_answer_response(user_state, user):
    """
    Generate response for as per the user state for all short answers under the
    ``problem_location`` root.
    Arguments:
        user_State (List): The user id for the user generating the report

    Returns:
            [Dict]: Returns a dictionaries
            containing the student aggregate result data.
    """
    user_answer = user_state['Answer']
    student_response_dict = {
        'username': user.username,
        'full_name': user.profile.name,
        'answer': user_answer,
    }

    return student_response_dict


def students_multiple_choice_response(user_states, user):
    """
    Generate response for as per the user state for all for
    problem(Multiple Choices and Single Choices)
    under the ``problem_location`` root.

    Arguments:
        user_State (List): The user id for the user generating the report

    Returns:
            [Dict]: Returns a dictionaries
            containing the student aggregate result data.
    """
    for user_state in user_states:
        user_answer = user_state['Answer']
        correct_answer = user_state['Correct Answer']
        user_answer_list = [x.strip() for x in user_answer.split("||")]
        correct_answer_list = [x.strip() for x in correct_answer.split("||")]
        student_response_dict = {
            'username': user.username,
            'full_name': user.profile.name,
            'answer': user_answer,
            'correct_answer': correct_answer,
            'earned_score': len(list(set(correct_answer_list).intersection(set(user_answer_list)))),
            'total_score': len(correct_answer_list),
        }

    return student_response_dict


def build_course_report_for_students(user_id, course_key, student_list):
    """
    Generate a list of problem responses for all problem under the
    ``problem_location`` root.
    Arguments:
        user_id (int): The user id for the user generating the report
        course_key (CourseKey): The ``CourseKey`` for the course whose report
            is being generated
    Returns:
            Tuple[List[Dict], List[str]]: Returns a list of dictionaries
            containing the student data which will be included in the
            final csv, and the features/keys to include in that CSV.
    """
    store = modulestore()
    user = get_user_model().objects.get(pk=user_id)
    usage_key = store.make_course_usage_key(course_key)
    user_state_client = DjangoXBlockUserStateClient()
    student_data = {}

    with store.bulk_operations(course_key):
        course_blocks = get_course_blocks(user, usage_key)

        for student_id in student_list:
            student_data[student_id] = []

            for _, _, block_key in build_problem_list(course_blocks, usage_key):
                # Chapter and sequential blocks are filtered out since they include state
                # which isn't useful for this report.
                if block_key.block_type in ('course', 'sequential', 'chapter', 'vertical'):
                    continue

                block = store.get_item(block_key)
                if not hasattr(block, 'is_exportable'):
                    continue
                if not block.is_exportable:
                    continue

                generated_report_data = defaultdict(list)

                # Blocks can implement the generate_report_data method to provide their own
                # human-readable formatting for user state.
                if hasattr(block, 'generate_report_data'):
                    try:
                        user_state_iterator = user_state_client.iter_all_for_block(
                            block_key, student_list=student_list)
                        for username, state in block.generate_report_data(user_state_iterator):
                            generated_report_data[username].append(state)
                    except NotImplementedError:
                        pass

                if block_key.block_type in ('problem'):
                    responses = get_problem_attributes(block.data, block_key)
                    responses['results'] = []
                    student = get_user_model().objects.get(pk=student_id)
                    user_states = generated_report_data.get(student.username)
                    if responses['problem_type'] in ProblemTypes.STRING_TYPE_PROBLEMS and user_states:
                        for user_state in user_states:
                            responses['results'].append({
                                'answer_id': user_state['Answer ID'],
                                'question': user_state['Question'],
                                'answer': user_state['Answer'],
                            })
                        student_data[student_id].append(responses)

    return student_data


def get_absolute_url(request, file):
    """
    return absolute url of a file
    """
    return request.build_absolute_uri(file.url) if file else None


def get_assessment_problem_data(course_key, user, request=None):
    """
    Generate skill assessment problem data from a course
    Args:
        request
        course_key (CourseKey): The ``CourseKey`` for the course whose data
            is being generated
        user (USER): user whose data will generate

    Returns:
        list[Dict]: Returns a list of dictionaries
    """
    assessments = []
    if request is None:
        request = RequestFactory().get(u'/')
        request.user = user

    course_outline_blocks = get_course_outline_block_tree(request, str(course_key), user)
    if course_outline_blocks:
        assessments = get_assessment_course_block([course_outline_blocks])

    return assessments


def get_assessment_course_block(course_blocks_children):
    """
    Generate assessment xblock usage key and type of that assessment xblock with in a course.
    Arguments:
        course_blocks_children (list[dict]): course block children data in form of tree
    Returns:
            list[Dict]: Returns a list of dictionaries
    """
    assessments = []
    for course_block in course_blocks_children:
        course_block_type = course_block.get('type')
        if course_block_type in ['genz_text_assessment', 'genz_rating_assessment']:
            return [{
                'id': course_block.get('id'),
                'type': course_block_type,
                'completion': course_block.get('completion')
            }]
        else:
            children = course_block.get('children')
            if children:
                assessments.extend(get_assessment_course_block(children))

    return assessments


def get_assessment_completion(assessments):
    """
    Compute the completion of skill assessment course for a student
    Args:
        assessments (list(dict)): skill assessment data in form of list of dict

    Returns:
        Boolean: Return a boolean
    """
    if not assessments:
        return False

    for assessment in assessments:
        if assessment.get('completion') < 1.0:
            return False

    return True


def get_student_unit_skills_assessment(user, course):
    assessment_data = get_assessment_problem_data(course.id, user)
    return get_assessment_completion(assessment_data) if assessment_data else None


def get_student_program_skills_assessment(student, gen_program=None):
    """
    Evaluate if student has completed his skill assessment

    Args:
        student: genplus student
        filter: filter only intro or outro assessment i-e possible values = 'intro' or 'outro'

    Returns: List[bool] of booleans

    """

    intro_assessments_completion = None
    outro_assessments_completion = None
    if gen_program is None:
        gen_program = student.active_class.program if student.active_class else None

    user = student.gen_user.user
    if user and gen_program is not None:
        if gen_program.intro_unit:
            intro_assessments_completion = get_student_unit_skills_assessment(user, gen_program.intro_unit)

        if gen_program.outro_unit:
            outro_assessments_completion = get_student_unit_skills_assessment(user, gen_program.outro_unit)

    return [intro_assessments_completion, outro_assessments_completion]


def get_user_assessment_result(user, raw_data, program):
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

    # get assessment usage key and type for program intro assessment course
    if program.intro_unit:
        assessments.extend(get_assessment_problem_data(program.intro_unit.id, user))

    # get assessment usage key and type for program outro assessment course
    if program.outro_unit:
        assessments.extend(get_assessment_problem_data(program.outro_unit.id, user))
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


def skill_reflection_response(skills, likert_questions, nuance_interrogation_questions):
    """
    This is to prepare a response for skill reflection combined view
    :param skills:
    :param likert_questions:
    :param nuance_interrogation_questions:
    :return: {}
    """
    _response = {
        'skills': skills,
        'intros': [],
        'outros': [],
        'nuance_interrogation': [],
    }

    def process_question_responses(questions, response_key, location_key):
        for question in questions:
            skill = question.skill.name
            submissions = list(question.submissions.filter(problem_location=getattr(question, location_key)).all())
            total_submissions = question.submissions.filter(problem_location=getattr(question, location_key)).count()
            stats = defaultdict(int)

            question_stats = {
                'qid': question.id,
                'skill': skill,
                'title': None,
                'submissions': [],
                'total_submissions': total_submissions
            }
            points_dict = {}

            for submission in submissions:
                question_response = submission.question_response
                response_text = question_response['student_response']['response_text']
                stats[response_text] += 1
                points_dict[response_text] = question_response['student_response']['points']
                if not question_stats['title']:
                    question_stats['title'] = question_response['question']

            if stats:
                for sk in stats.keys():
                    question_stats['submissions'].append({'key': sk, "value": stats[sk], 'points': points_dict[sk]})

                _response[response_key].append(question_stats)

    process_question_responses(likert_questions, 'intros', 'start_unit_location')
    process_question_responses(likert_questions, 'outros', 'end_unit_location')
    process_question_responses(nuance_interrogation_questions, 'nuance_interrogation', 'start_unit_location')

    def populate_likerts():
        question_map = {}
        for intro, outro in itertools.zip_longest(_response['intros'], _response['outros']):
            question_map[intro['qid']] = question_map.get(intro['qid'], {
                'title':intro['title'],
                'skill':intro['skill'],
            })
            if intro:
                question_map[intro['qid']]['intro'] = intro
            if outro:
                question_map[intro['qid']]['outro'] = outro
        return question_map.values()

    response = {
        'skills': skills,
        'likerts': populate_likerts(),
        'nuance_interrogation': _response['nuance_interrogation'],
    }

    return response


def skill_reflection_individual_response(skills, likert_questions, nuance_interrogation_questions, user_id):
    """
    This is to prepare a response for skill reflection combined view
    :param skills:
    :param likert_questions:
    :param nuance_interrogation_questions:
    :return: {}
    """
    response = {
        'skills': skills,
        'intros': [],
        'outros': [],
        'nuance_interrogation': [],
    }

    def process_question_responses(questions, response_key, location_key):
        for question in questions:
            skill = question.skill.name
            submission = question.submissions.filter(
                user_id=user_id, problem_location=getattr(question, location_key),
            ).first()
            if submission:
                question_response = submission.question_response
                response_text = question_response['student_response']['response_text']
                response[response_key].append({'skill': skill, 'response_text': response_text})

    process_question_responses(likert_questions, 'intros', 'start_unit_location')
    process_question_responses(likert_questions, 'outros', 'end_unit_location')
    process_question_responses(nuance_interrogation_questions, 'nuance_interrogation', 'start_unit_location')
    return response
