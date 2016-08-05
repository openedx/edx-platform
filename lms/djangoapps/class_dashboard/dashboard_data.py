"""
Computes the data to display on the Instructor Dashboard
"""
from collections import defaultdict
from util.json_request import JsonResponse
import json

from courseware import models
from django.conf import settings
from django.db.models import Count
from django.utils.translation import ugettext as _

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata
from instructor_analytics.csvs import create_csv_response
from analyticsclient.client import Client
from analyticsclient.exceptions import NotFoundError
from student.models import CourseAccessRole
from opaque_keys.edx import locator
from opaque_keys.edx.locations import SlashSeparatedCourseKey

# Used to limit the length of list displayed to the screen.
MAX_SCREEN_LIST_LENGTH = 250
PROB_TYPE_LIST = [
    'problem',
    'lti',
]

# exclude these in Metrics
NON_STUDENT_ROLES = ['instructor', 'staff']


def get_non_student_list(course_key):
    """
    Find all user_ids with instructor or staff roles in student_courseaccessrole table
    """
    non_students = CourseAccessRole.objects.filter(
        course_id=course_key,
        role__in=NON_STUDENT_ROLES,
    ).values('user_id').distinct()

    return [non_student['user_id'] for non_student in non_students]


def get_problem_grade_distribution(course_id, enrollment):
    """
    Returns the grade distribution per problem for the course

    `course_id` the course ID for the course interested in

    `enrollment` the number of students enrolled in this course.

    Output is 2 dicts:
      'prob-grade_distrib' where the key is the problem 'module_id' and the value is a dict with:
        'max_grade' - max grade for this problem
        'grade_distrib' - array of tuples (`grade`,`count`).
      'total_student_count' where the key is problem 'module_id' and the value is number of students
        attempting the problem
    """
    non_student_list = get_non_student_list(course_id)

    prob_grade_distrib = {}
    total_student_count = defaultdict(int)

    if enrollment <= settings.MAX_ENROLLEES_FOR_METRICS_USING_DB or not settings.ANALYTICS_DATA_URL:
        # Aggregate query on studentmodule table for grade data for all problems in course
        queryset = models.StudentModule.objects.filter(
            course_id__exact=course_id,
            grade__isnull=False,
            module_type__in=PROB_TYPE_LIST,
        ).exclude(student_id__in=non_student_list).values('module_state_key', 'grade', 'max_grade').annotate(count_grade=Count('grade'))

        # Loop through resultset building data for each problem
        for row in queryset:
            curr_problem = course_id.make_usage_key_from_deprecated_string(row['module_state_key'])

            # Build set of grade distributions for each problem that has student responses
            if curr_problem in prob_grade_distrib:
                prob_grade_distrib[curr_problem]['grade_distrib'].append((row['grade'], row['count_grade']))

                if ((prob_grade_distrib[curr_problem]['max_grade'] != row['max_grade']) and
                        (prob_grade_distrib[curr_problem]['max_grade'] < row['max_grade'])):
                    prob_grade_distrib[curr_problem]['max_grade'] = row['max_grade']

            else:
                prob_grade_distrib[curr_problem] = {
                    'max_grade': row['max_grade'],
                    'grade_distrib': [(row['grade'], row['count_grade']), ],
                }

            # Build set of total students attempting each problem
            total_student_count[curr_problem] += row['count_grade']
    else:
        # Retrieve course object down to problems
        course = modulestore().get_course(course_id, depth=4)

        # Connect to analytics data client
        client = Client(base_url=settings.ANALYTICS_DATA_URL, auth_token=settings.ANALYTICS_DATA_TOKEN)

        for section in course.get_children():
            for subsection in section.get_children():
                for unit in subsection.get_children():
                    for child in unit.get_children():
                        if child.location.category not in PROB_TYPE_LIST:
                            continue

                        problem_id = child.location
                        problem = client.modules(course_id, problem_id)

                        try:
                            grade_distribution = problem.grade_distribution()
                        except NotFoundError:
                            grade_distribution = []

                        for score in grade_distribution:
                            total_student_count[problem_id] += score['count']

                            if problem_id in prob_grade_distrib:
                                if prob_grade_distrib[problem_id]['max_grade'] < score['max_grade']:
                                    prob_grade_distrib[problem_id]['max_grade'] = score['max_grade']

                                prob_grade_distrib[problem_id]['grade_distrib'].append((score['grade'], score['count']))
                            else:
                                prob_grade_distrib[problem_id] = {
                                    'max_grade': score['max_grade'],
                                    'grade_distrib': [(score['grade'], score['count']), ],
                                }

    return prob_grade_distrib, total_student_count


def get_sequential_open_distrib(course_id, enrollment):
    """
    Returns the number of students that opened each subsection/sequential of the course

    `course_id` the course ID for the course interested in

    `enrollment` the number of students enrolled in this course.

    Outputs a dict mapping the 'module_id' to the number of students that have opened that subsection/sequential.
    """
    sequential_open_distrib = {}

    non_student_list = get_non_student_list(course_id)

    if enrollment <= settings.MAX_ENROLLEES_FOR_METRICS_USING_DB or not settings.ANALYTICS_DATA_URL:
        # Aggregate query on studentmodule table for "opening a subsection" data
        queryset = models.StudentModule.objects.filter(
            course_id__exact=course_id,
            module_type__exact='sequential',
        ).exclude(student_id__in=non_student_list).values('module_state_key').annotate(count_sequential=Count('module_state_key'))

        for row in queryset:
            module_id = course_id.make_usage_key_from_deprecated_string(row['module_state_key'])
            sequential_open_distrib[module_id] = row['count_sequential']
    else:
        # Retrieve course object down to subsection
        course = modulestore().get_course(course_id, depth=2)

        # Connect to analytics data client
        client = Client(base_url=settings.ANALYTICS_DATA_URL, auth_token=settings.ANALYTICS_DATA_TOKEN)

        for section in course.get_children():
            for subsection in section.get_children():
                module = client.modules(course_id, subsection.location)

                try:
                    sequential_open = module.sequential_open_distribution()
                except NotFoundError:
                    pass
                else:
                    sequential_open_distrib[subsection.location] = sequential_open[0]['count']

    return sequential_open_distrib


def get_problem_set_grade_distrib(course_id, problem_set, enrollment):
    """
    Returns the grade distribution for the problems specified in `problem_set`.

    `course_id` the course ID for the course interested in

    `problem_set` an array of UsageKeys representing problem module_id's.

    `enrollment` the number of students enrolled in this course.

    Requests from the database the a count of each grade for each problem in the `problem_set`.

    Returns a dict, where the key is the problem 'module_id' and the value is a dict with two parts:
      'max_grade' - the maximum grade possible for the course
      'grade_distrib' - array of tuples (`grade`,`count`) ordered by `grade`
    """

    non_student_list = get_non_student_list(course_id)

    prob_grade_distrib = {}

    if enrollment <= settings.MAX_ENROLLEES_FOR_METRICS_USING_DB or not settings.ANALYTICS_DATA_URL:
        # Aggregate query on studentmodule table for grade data for set of problems in course
        queryset = models.StudentModule.objects.filter(
            course_id__exact=course_id,
            grade__isnull=False,
            module_type__in=PROB_TYPE_LIST,
            module_state_key__in=problem_set,
        ).exclude(student_id__in=non_student_list).values(
            'module_state_key',
            'grade',
            'max_grade',
        ).annotate(count_grade=Count('grade')).order_by('module_state_key', 'grade')

        # Loop through resultset building data for each problem
        for row in queryset:
            problem_id = course_id.make_usage_key_from_deprecated_string(row['module_state_key'])
            if problem_id not in prob_grade_distrib:
                prob_grade_distrib[problem_id] = {
                    'max_grade': 0,
                    'grade_distrib': [],
                }

            curr_grade_distrib = prob_grade_distrib[problem_id]
            curr_grade_distrib['grade_distrib'].append((row['grade'], row['count_grade']))

            if curr_grade_distrib['max_grade'] < row['max_grade']:
                curr_grade_distrib['max_grade'] = row['max_grade']
    else:
        # Connect to analytics data client
        client = Client(base_url=settings.ANALYTICS_DATA_URL, auth_token=settings.ANALYTICS_DATA_TOKEN)

        for problem in problem_set:
            module = client.modules(course_id, problem)

            try:
                grade_distribution = module.grade_distribution()
            except NotFoundError:
                grade_distribution = []

            for score in grade_distribution:
                if problem in prob_grade_distrib:
                    if prob_grade_distrib[problem]['max_grade'] < score['max_grade']:
                        prob_grade_distrib[problem]['max_grade'] = score['max_grade']

                    prob_grade_distrib[problem]['grade_distrib'].append((score['grade'], score['count']))
                else:
                    prob_grade_distrib[problem] = {
                        'max_grade': score['max_grade'],
                        'grade_distrib': [(score['grade'], score['count'])],
                    }

    return prob_grade_distrib


def construct_problem_data(prob_grade_distrib, total_student_count, c_subsection, c_unit, c_problem, component):
    """
    Returns dict of problem with student grade data.

    `prob_grade_distrib` Dict of grade distribution for all problems in the course.
    `total_student_count` Dict of number of students attempting each problem.
    `c_subsection` Incremental subsection count.
    `c_unit` Incremental unit count.
    `c_problem` Incremental problem count.
    `component` The component for which data is being returned.

    Returns a dict of problem label and data for use in d3 rendering.
    """
    c_problem += 1
    stack_data = []

    # Construct label to display for this problem
    label = "P{0}.{1}.{2}".format(c_subsection, c_unit, c_problem)

    if component.location in prob_grade_distrib:
        problem_info = prob_grade_distrib[component.location]

        # Get problem_name for tooltip
        problem_name = own_metadata(component).get('display_name', '')

        # Compute percent of this grade over max_grade
        max_grade = float(problem_info['max_grade'])
        for (grade, count_grade) in problem_info['grade_distrib']:
            percent = 0.0
            if max_grade > 0:
                percent = round((grade * 100.0) / max_grade, 1)

            # Compute percent of students with this grade
            student_count_percent = 0

            if total_student_count[component.location] > 0:
                student_count_percent = count_grade * 100 / total_student_count[component.location]

            # Tooltip parameters for problem in grade distribution view
            tooltip = {
                'type': 'problem',
                'label': label,
                'problem_name': problem_name,
                'count_grade': count_grade,
                'percent': percent,
                'grade': grade,
                'max_grade': max_grade,
                'student_count_percent': student_count_percent,
            }

            # Construct data to be sent to d3
            stack_data.append({
                'color': percent,
                'value': count_grade,
                'tooltip': tooltip,
                'module_url': component.location.to_deprecated_string(),
            })

    problem = {
        'xValue': label,
        'stackData': stack_data,
    }
    return problem, c_problem


def get_d3_problem_grade_distrib(course_id, enrollment):
    """
    Returns problem grade distribution information for each section, data already in format for d3 function.

    `course_id` the course ID for the course interested in

    `enrollment` the number of students enrolled in this course.

    Returns an array of dicts in the order of the sections. Each dict has:
      'display_name' - display name for the section
      'data' - data for the d3_stacked_bar_graph function of the grade distribution for that problem
    """

    d3_data = []

    prob_grade_distrib, total_student_count = get_problem_grade_distribution(course_id, enrollment)

    # Retrieve course object down to problems
    course = modulestore().get_course(course_id, depth=4)

    # Iterate through sections, subsections, units, problems
    for section in course.get_children():
        curr_section = {}
        curr_section['display_name'] = own_metadata(section).get('display_name', '')
        data = []
        c_subsection = 0
        for subsection in section.get_children():
            c_subsection += 1
            c_unit = 0
            for unit in subsection.get_children():
                c_unit += 1
                c_problem = 0
                for child in unit.get_children():

                    # Student data is at the problem level
                    if child.location.category in PROB_TYPE_LIST:
                        problem, c_problem = construct_problem_data(
                            prob_grade_distrib,
                            total_student_count,
                            c_subsection,
                            c_unit,
                            c_problem,
                            child
                        )
                        data.append(problem)
                    elif child.location.category in settings.TYPES_WITH_CHILD_PROBLEMS_LIST:
                        for library_problem in child.get_children():
                            problem, c_problem = construct_problem_data(
                                prob_grade_distrib,
                                total_student_count,
                                c_subsection,
                                c_unit,
                                c_problem,
                                library_problem
                            )
                            data.append(problem)
        curr_section['data'] = data

        d3_data.append(curr_section)

    return d3_data


def get_d3_sequential_open_distrib(course_id, enrollment):
    """
    Returns how many students opened a sequential/subsection for each section, data already in format for d3 function.

    `course_id` the course ID for the course interested in

    `enrollment` the number of students enrolled in this course.

    Returns an array in the order of the sections and each dict has:
      'display_name' - display name for the section
      'data' - data for the d3_stacked_bar_graph function of how many students opened each sequential/subsection
    """

    d3_data = []

    # Retrieve course object down to subsection
    course = modulestore().get_course(course_id, depth=2)

    sequential_open_distrib = get_sequential_open_distrib(course_id, enrollment)

    # Iterate through sections, subsections
    for section in course.get_children():
        curr_section = {}
        curr_section['display_name'] = own_metadata(section).get('display_name', '')
        data = []
        c_subsection = 0

        # Construct data for each subsection to be sent to d3
        for subsection in section.get_children():
            c_subsection += 1
            subsection_name = own_metadata(subsection).get('display_name', '')

            if subsection.location in sequential_open_distrib:
                open_count = sequential_open_distrib[subsection.location]
            else:
                open_count = 0

            stack_data = []

            # Tooltip parameters for subsection in open_distribution view
            tooltip = {
                'type': 'subsection',
                'num_students': open_count,
                'subsection_num': c_subsection,
                'subsection_name': subsection_name,
            }

            stack_data.append({
                'color': 0,
                'value': open_count,
                'tooltip': tooltip,
                'module_url': subsection.location.to_deprecated_string(),
            })
            subsection = {
                'xValue': "SS {0}".format(c_subsection),
                'stackData': stack_data,
            }
            data.append(subsection)

        curr_section['data'] = data
        d3_data.append(curr_section)

    return d3_data


def get_d3_section_grade_distrib(course_id, section, enrollment):
    """
    Returns the grade distribution for the problems in the `section` section in a format for the d3 code.

    `course_id` a string that is the course's ID.

    `section` an int that is a zero-based index into the course's list of sections.

    `enrollment` the number of students enrolled in this course.

    Navigates to the section specified to find all the problems associated with that section and then finds the grade
    distribution for those problems. Finally returns an object formated the way the d3_stacked_bar_graph.js expects its
    data object to be in.

    If this is requested multiple times quickly for the same course, it is better to call
    get_d3_problem_grade_distrib and pick out the sections of interest.

    Returns an array of dicts with the following keys (taken from d3_stacked_bar_graph.js's documentation)
      'xValue' - Corresponding value for the x-axis
      'stackData' - Array of objects with key, value pairs that represent a bar:
        'color' - Defines what "color" the bar will map to
        'value' - Maps to the height of the bar, along the y-axis
        'tooltip' - (Optional) Text to display on mouse hover
    """
    # Retrieve course object down to problems
    course = modulestore().get_course(course_id, depth=4)

    problem_set = []
    problem_info = {}
    c_subsection = 0
    for subsection in course.get_children()[section].get_children():
        c_subsection += 1
        c_unit = 0
        for unit in subsection.get_children():
            c_unit += 1
            c_problem = 0
            for child in unit.get_children():
                if child.location.category in PROB_TYPE_LIST:
                    c_problem += 1
                    problem_set.append(child.location)
                    problem_info[child.location] = {
                        'id': child.location.to_deprecated_string(),
                        'x_value': "P{0}.{1}.{2}".format(c_subsection, c_unit, c_problem),
                        'display_name': own_metadata(child).get('display_name', ''),
                    }
                elif child.location.category in settings.TYPES_WITH_CHILD_PROBLEMS_LIST:
                    for library_problem in child.get_children():
                        c_problem += 1
                        problem_set.append(library_problem.location)
                        problem_info[library_problem.location] = {
                            'id': library_problem.location.to_deprecated_string(),
                            'x_value': "P{0}.{1}.{2}".format(c_subsection, c_unit, c_problem),
                            'display_name': own_metadata(library_problem).get('display_name', ''),
                        }

    grade_distrib = get_problem_set_grade_distrib(course_id, problem_set, enrollment)

    d3_data = []

    # Construct data for each problem to be sent to d3
    for problem in problem_set:
        stack_data = []

        if problem in grade_distrib:
            max_grade = float(grade_distrib[problem]['max_grade'])
            for (grade, count_grade) in grade_distrib[problem]['grade_distrib']:
                percent = 0.0
                if max_grade > 0:
                    percent = round((grade * 100.0) / max_grade, 1)

                # Construct tooltip for problem in grade distibution view
                tooltip = {
                    'type': 'problem',
                    'problem_info_x': problem_info[problem]['x_value'],
                    'count_grade': count_grade,
                    'percent': percent,
                    'problem_info_n': problem_info[problem]['display_name'],
                    'grade': grade,
                    'max_grade': max_grade,
                }

                stack_data.append({
                    'color': percent,
                    'value': count_grade,
                    'tooltip': tooltip,
                })

        d3_data.append({
            'xValue': problem_info[problem]['x_value'],
            'stackData': stack_data,
        })

    return d3_data


def get_section_display_name(course_id):
    """
    Returns an array of the display names for each section in the course.

    `course_id` the course ID for the course interested in

    The ith string in the array is the display name of the ith section in the course.
    """

    course = modulestore().get_course(course_id, depth=4)

    section_display_name = [""] * len(course.get_children())
    i = 0
    for section in course.get_children():
        section_display_name[i] = own_metadata(section).get('display_name', '')
        i += 1

    return section_display_name


def get_array_section_has_problem(course_id):
    """
    Returns an array of true/false whether each section has problems.

    `course_id` the course ID for the course interested in

    The ith value in the array is true if the ith section in the course contains problems and false otherwise.
    """

    course = modulestore().get_course(course_id, depth=4)

    b_section_has_problem = [False] * len(course.get_children())
    i = 0
    for section in course.get_children():
        for subsection in section.get_children():
            for unit in subsection.get_children():
                for child in unit.get_children():
                    if child.location.category in PROB_TYPE_LIST:
                        b_section_has_problem[i] = True
                        break  # out of child loop
                    elif child.location.category in settings.TYPES_WITH_CHILD_PROBLEMS_LIST:
                        for library_problem in child.get_children():
                            if library_problem.location.category in PROB_TYPE_LIST:
                                b_section_has_problem[i] = True
                                break  # out of child loop
                if b_section_has_problem[i]:
                    break  # out of unit loop
            if b_section_has_problem[i]:
                break  # out of subsection loop

        i += 1

    return b_section_has_problem


def get_students_opened_subsection(request, csv=False):
    """
    Get a list of students that opened a particular subsection.
    If 'csv' is False, returns a dict of student's name: username.

    If 'csv' is True, returns a header array, and an array of arrays in the format:
    student names, usernames for CSV download.
    """
    csv = request.GET.get('csv')
    course_id = request.GET.get('course_id')
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    module_state_key = course_key.make_usage_key_from_deprecated_string(request.GET.get('module_id'))

    non_student_list = get_non_student_list(course_key)

    # Query for "opened a subsection" students
    students = models.StudentModule.objects.select_related('student').filter(
        module_state_key__exact=module_state_key,
        module_type__exact='sequential',
    ).exclude(student_id__in=non_student_list).values('student__id', 'student__username', 'student__profile__name').order_by('student__profile__name')

    results = []

    if not csv:
        # Restrict screen list length
        # Adding 1 so can tell if list is larger than MAX_SCREEN_LIST_LENGTH
        # without doing another select.
        for student in students[0:MAX_SCREEN_LIST_LENGTH + 1]:
            results.append({
                'name': student['student__profile__name'],
                'username': student['student__username'],
            })
        max_exceeded = False
        if len(results) > MAX_SCREEN_LIST_LENGTH:
            # Remove the last item so list length is exactly MAX_SCREEN_LIST_LENGTH
            del results[-1]
            max_exceeded = True
        response_payload = {
            'results': results,
            'max_exceeded': max_exceeded,
        }
        return JsonResponse(response_payload)
    else:
        tooltip = request.GET.get('tooltip')

        # Subsection name is everything after 3rd space in tooltip
        filename = sanitize_filename(' '.join(tooltip.split(' ')[3:]))
        header = [_("Name").encode('utf-8'), _("Username").encode('utf-8')]
        for student in students:
            results.append([student['student__profile__name'], student['student__username']])

        response = create_csv_response(filename, header, results)
        return response


def get_students_problem_grades(request, csv=False):
    """
    Get a list of students and grades for a particular problem.
    If 'csv' is False, returns a dict of student's name: username: grade: percent.

    If 'csv' is True, returns a header array, and an array of arrays in the format:
    student names, usernames, grades, percents for CSV download.
    """
    csv = request.GET.get('csv')
    course_id = request.GET.get('course_id')
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    module_state_key = course_key.make_usage_key_from_deprecated_string(request.GET.get('module_id'))

    non_student_list = get_non_student_list(course_key)

    # Query for "problem grades" students
    students = models.StudentModule.objects.select_related('student').filter(
        module_state_key=module_state_key,
        module_type__in=PROB_TYPE_LIST,
        grade__isnull=False,
    ).exclude(student_id__in=non_student_list).values('student__username', 'student__profile__name', 'grade', 'max_grade').order_by('student__profile__name')

    results = []

    if not csv:
        # Restrict screen list length
        # Adding 1 so can tell if list is larger than MAX_SCREEN_LIST_LENGTH
        # without doing another select.
        for student in students[0:MAX_SCREEN_LIST_LENGTH + 1]:
            student_dict = {
                'name': student['student__profile__name'],
                'username': student['student__username'],
                'grade': student['grade'],
            }

            student_dict['percent'] = 0
            if student['max_grade'] > 0:
                student_dict['percent'] = round(student['grade'] * 100 / student['max_grade'])
            results.append(student_dict)
        max_exceeded = False
        if len(results) > MAX_SCREEN_LIST_LENGTH:
            # Remove the last item so list length is exactly MAX_SCREEN_LIST_LENGTH
            del results[-1]
            max_exceeded = True

        response_payload = {
            'results': results,
            'max_exceeded': max_exceeded,
        }
        return JsonResponse(response_payload)
    else:
        tooltip = request.GET.get('tooltip')
        filename = sanitize_filename(tooltip[:tooltip.rfind(' - ')])

        header = [_("Name").encode('utf-8'), _("Username").encode('utf-8'), _("Grade").encode('utf-8'), _("Percent").encode('utf-8')]
        for student in students:
            percent = 0
            if student['max_grade'] > 0:
                percent = round(student['grade'] * 100 / student['max_grade'])
            results.append([student['student__profile__name'], student['student__username'], student['grade'], percent])

        response = create_csv_response(filename, header, results)
        return response


def post_metrics_data_csv(request):
    """
    Generate a list of opened subsections or problems for the entire course for CSV download.
    Returns a header array, and an array of arrays in the format:
    section, subsection, count of students for subsections
    or section, problem, name, count of students, percent of students, score for problems.
    """

    data = json.loads(request.POST['data'])
    sections = json.loads(data['sections'])
    tooltips = json.loads(data['tooltips'])
    course_id = data['course_id']
    data_type = data['data_type']

    results = []
    if data_type == 'subsection':
        header = [_("Section").encode('utf-8'), _("Subsection").encode('utf-8'), _("Opened by this number of students").encode('utf-8')]
        filename = sanitize_filename(_('subsections') + '_' + course_id)
    elif data_type == 'problem':
        header = [_("Section").encode('utf-8'), _("Problem").encode('utf-8'), _("Name").encode('utf-8'), _("Count of Students").encode('utf-8'), _("Percent of Students").encode('utf-8'), _("Score").encode('utf-8')]
        filename = sanitize_filename(_('problems') + '_' + course_id)

    for index, section in enumerate(sections):
        results.append([section])

        # tooltips array is array of dicts for subsections and
        # array of array of dicts for problems.
        if data_type == 'subsection':
            for tooltip_dict in tooltips[index]:
                num_students = tooltip_dict['num_students']
                subsection = tooltip_dict['subsection_name']
                # Append to results offsetting 1 column to the right.
                results.append(['', subsection, num_students])

        elif data_type == 'problem':
            for tooltip in tooltips[index]:
                for tooltip_dict in tooltip:
                    label = tooltip_dict['label']
                    problem_name = tooltip_dict['problem_name']
                    count_grade = tooltip_dict['count_grade']
                    student_count_percent = tooltip_dict['student_count_percent']
                    percent = tooltip_dict['percent']
                    # Append to results offsetting 1 column to the right.
                    results.append(['', label, problem_name, count_grade, student_count_percent, percent])

    response = create_csv_response(filename, header, results)
    return response


def sanitize_filename(filename):
    """
    Utility function
    """
    filename = filename.replace(" ", "_")
    filename = filename.encode('utf-8')
    filename = filename[0:25] + '.csv'
    return filename
