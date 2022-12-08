from lxml import etree
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import UsageKey
from collections import defaultdict

from django.contrib.auth import get_user_model
from openedx.features.course_experience.utils import get_course_outline_block_tree
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.courseware.user_state_client import DjangoXBlockUserStateClient


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
    usage_key = UsageKey.from_string(usage_key_str).map_into_course(course_key)
    user = get_user_model().objects.get(pk=user_id)

    if single_problem is True:
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
                        block_key)
                    for username, state in block.generate_report_data(user_state_iterator):
                        generated_report_data[username].append(state)
                except NotImplementedError:
                    pass

            responses = {}

            if block_key.block_type in ('problem'):
                responses = get_problem_attributes(block.data, block_key)
                aggregate_result = {}
                user_short_answers = {}
                if responses['problem_type'] in ('single_choice', 'multiple_choice'):
                    responses['results'] = []
                else:
                    responses['results'] = {}
                    
                for user_id in student_list:
                    user = get_user_model().objects.get(pk=user_id)
                    user_states = generated_report_data.get(user.username)
                    if user_states:
                        # For each response in the block, aggregate the result for the problem, and add in the responses
                        if responses['problem_type'] in ('single_choice', 'multiple_choice'):
                            if filter_type == "aggregate_response":
                                aggregate_result.update(students_aggregate_result(
                                    user_states, aggregate_result))
                            elif filter_type == "individual_response":
                                responses['results'].append(
                                    students_multiple_choice_response(user_states, user))
                        elif responses['problem_type'] == "short_answers":
                            for user_state in user_states:
                                answer_id = problem_id if problem_id is not None else user_state['Answer ID']
                                if answer_id not in user_short_answers:
                                    user_short_answers[answer_id] = {
                                        'question_text': user_state['Question'],
                                        'answer_id': user_state['Answer ID'],
                                        'answers': [get_students_short_answer_response(user_state, user)] if answer_id == user_state['Answer ID'] else []
                                    }
                                else:
                                    if answer_id == user_state['Answer ID']:
                                        user_short_answers[answer_id]['answers'].append(
                                            get_students_short_answer_response(user_state, user))

                if responses['problem_type'] == 'short_answers' and len(user_short_answers) > 0:
                    responses['results'].update(user_short_answers)
                        
                if responses['problem_type'] in ('single_choice', 'multiple_choice') and filter_type == "aggregate_response":
                    for key, value in aggregate_result.items():
                        responses['results'].append({
                            'title': key,
                            'count': value['count'],
                            'is_correct': value['is_correct'],
                        })

                if responses['problem_type'] in ('single_choice', 'multiple_choice', 'short_answers') and single_problem is not True:
                    student_data.append(responses)
                else:
                    student_data.update(responses)

    return student_data


def students_aggregate_result(user_states, aggregate_result):
    """
    Generate aggregate response for problem(Multiple Choices and Single Choices) as per the user state  under the
    ``problem_location`` root.
    Arguments:
        user_State (List): The user id for the user generating the report

    Returns:
            [Dict]: Returns a dictionaries
            containing the students aggregate result data.
    """
    for user_state in user_states:
        user_answer = user_state['Answer']
        correct_answer = user_state['Correct Answer']
        if user_answer not in aggregate_result:
            aggregate_result[user_answer] = {
                'count': 1,
                'is_correct': correct_answer == user_answer
            }
        else:
            aggregate_result[user_answer]['count'] += 1

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
        elif e.text and e.attrib.get('class') == 'question-text' and responses['problem_type'] != "short_answers":
            responses['question_text'] = e.text
        elif e.text and e.tag == 'choice':
            choice_dict = {
                'statement': e.text,
                'correct': e.attrib.get('correct')
            }
            if e.attrib.get('correct') == 'true':
                responses['selection'] += 1
            data_dict.update({e.attrib.get('class'): choice_dict})
    if responses['problem_type'] != "short_answers":
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
        'full_name': user.get_full_name(),
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
        user_answer_list = [x.strip() for x in user_answer.split(",")]
        correct_answer_list = [x.strip() for x in correct_answer.split(",")]
        student_response_dict = {
            'username': user.username,
            'full_name': user.get_full_name(),
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
                            block_key)
                        for username, state in block.generate_report_data(user_state_iterator):
                            generated_report_data[username].append(state)
                    except NotImplementedError:
                        pass

                if block_key.block_type in ('problem'):
                    responses = get_problem_attributes(block.data, block_key)
                    responses['results'] = []
                    student = get_user_model().objects.get(pk=student_id)
                    user_states = generated_report_data.get(student.username)
                    if responses['problem_type'] == 'short_answers' and user_states:
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

def get_assessment_problem_data(request, course_key, user):
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
    course_outline_blocks = get_course_outline_block_tree(request, str(course_key), user)
    if course_outline_blocks:
        course_blocks_children = course_outline_blocks.get('children')
        assessments = get_assessment_course_block(course_blocks_children)

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
                'completion':  course_block.get('completion')
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
    for assessment in assessments:
        if assessment.get('completion') == 0.0:
            return False

    return True
