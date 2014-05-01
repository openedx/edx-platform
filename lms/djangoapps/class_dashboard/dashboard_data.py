"""
Computes the data to display on the Instructor Dashboard
"""
from util.json_request import JsonResponse

from courseware import models
from django.db.models import Count
from django.utils.translation import ugettext as _

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata
from analytics.csvs import create_csv_response

from xmodule.modulestore import Location

# Used to limit the length of list displayed to the screen.
MAX_SCREEN_LIST_LENGTH = 250

def get_problem_grade_distribution(course_id):
    """
    Returns the grade distribution per problem for the course

    `course_id` the course ID for the course interested in

    Output is a dict, where the key is the problem 'module_id' and the value is a dict with:
        'max_grade' - max grade for this problem
        'grade_distrib' - array of tuples (`grade`,`count`).
    """

    # Aggregate query on studentmodule table for grade data for all problems in course
    db_query = models.StudentModule.objects.filter(
        course_id__exact=course_id,
        grade__isnull=False,
        module_type__exact="problem",
    ).values('module_id', 'grade', 'max_grade').annotate(count_grade=Count('grade'))

    prob_grade_distrib = {}

    # Loop through resultset building data for each problem
    for row in db_query:
        curr_problem = course_id.make_usage_key_from_deprecated_string(row['module_id'])

        # Build set of grade distributions for each problem that has student responses
        if curr_problem in prob_grade_distrib:
            prob_grade_distrib[curr_problem]['grade_distrib'].append((row['grade'], row['count_grade']))

            if (prob_grade_distrib[curr_problem]['max_grade'] != row['max_grade']) and \
                    (prob_grade_distrib[curr_problem]['max_grade'] < row['max_grade']):
                prob_grade_distrib[curr_problem]['max_grade'] = row['max_grade']

        else:
            prob_grade_distrib[curr_problem] = {
                'max_grade': row['max_grade'],
                'grade_distrib': [(row['grade'], row['count_grade'])]
            }

    return prob_grade_distrib


def get_sequential_open_distrib(course_id):
    """
    Returns the number of students that opened each subsection/sequential of the course

    `course_id` the course ID for the course interested in

    Outputs a dict mapping the 'module_id' to the number of students that have opened that subsection/sequential.
    """

    # Aggregate query on studentmodule table for "opening a subsection" data
    db_query = models.StudentModule.objects.filter(
        course_id__exact=course_id,
        module_type__exact="sequential",
    ).values('module_id').annotate(count_sequential=Count('module_id'))

    # Build set of "opened" data for each subsection that has "opened" data
    sequential_open_distrib = {}
    for row in db_query:
        sequential_open_distrib[row['module_id']] = row['count_sequential']

    return sequential_open_distrib


def get_problem_set_grade_distrib(course_id, problem_set):
    """
    Returns the grade distribution for the problems specified in `problem_set`.

    `course_id` the course ID for the course interested in

    `problem_set` an array of UsageKeys representing problem module_id's.

    Requests from the database the a count of each grade for each problem in the `problem_set`.

    Returns a dict, where the key is the problem 'module_id' and the value is a dict with two parts:
      'max_grade' - the maximum grade possible for the course
      'grade_distrib' - array of tuples (`grade`,`count`) ordered by `grade`
    """

    # Aggregate query on studentmodule table for grade data for set of problems in course
    db_query = models.StudentModule.objects.filter(
        course_id__exact=course_id,
        grade__isnull=False,
        module_type__exact="problem",
        module_id__in=[location.replace(run=None) for location in problem_set],
    ).values(
        'module_id',
        'grade',
        'max_grade',
    ).annotate(count_grade=Count('grade')).order_by('module_id', 'grade')

    prob_grade_distrib = {}

    # Loop through resultset building data for each problem
    for row in db_query:
        row_loc = course_id.make_usage_key_from_deprecated_string(row['module_id'])
        if row_loc not in prob_grade_distrib:
            prob_grade_distrib[row_loc] = {
                'max_grade': 0,
                'grade_distrib': [],
            }

        curr_grade_distrib = prob_grade_distrib[row_loc]
        curr_grade_distrib['grade_distrib'].append((row['grade'], row['count_grade']))

        if curr_grade_distrib['max_grade'] < row['max_grade']:
            curr_grade_distrib['max_grade'] = row['max_grade']

    return prob_grade_distrib


def get_d3_problem_grade_distrib(course_id):
    """
    Returns problem grade distribution information for each section, data already in format for d3 function.

    `course_id` the course ID for the course interested in

    Returns an array of dicts in the order of the sections. Each dict has:
      'display_name' - display name for the section
      'data' - data for the d3_stacked_bar_graph function of the grade distribution for that problem
    """

    prob_grade_distrib = get_problem_grade_distribution(course_id)
    d3_data = []

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
                    if child.location.category == 'problem':
                        c_problem += 1
                        stack_data = []

                        # Construct label to display for this problem
                        label = "P{0}.{1}.{2}".format(c_subsection, c_unit, c_problem)

                        # Only problems in prob_grade_distrib have had a student submission.
                        if child.location in prob_grade_distrib:

                            # Get max_grade, grade_distribution for this problem
                            problem_info = prob_grade_distrib[child.location]

                            # Get problem_name for tooltip
                            problem_name = own_metadata(child).get('display_name', '')

                            # Compute percent of this grade over max_grade
                            max_grade = float(problem_info['max_grade'])
                            for (grade, count_grade) in problem_info['grade_distrib']:
                                percent = 0.0
                                if max_grade > 0:
                                    percent = (grade * 100.0) / max_grade

                                # Construct tooltip for problem in grade distibution view
                                tooltip = _("{label} {problem_name} - {count_grade} {students} ({percent:.0f}%: {grade:.0f}/{max_grade:.0f} {questions})").format(
                                    label=label,
                                    problem_name=problem_name,
                                    count_grade=count_grade,
                                    students=_("students"),
                                    percent=percent,
                                    grade=grade,
                                    max_grade=max_grade,
                                    questions=_("questions"),
                                )

                                # Construct data to be sent to d3
                                stack_data.append({
                                    'color': percent,
                                    'value': count_grade,
                                    'tooltip': tooltip,
                                    'module_url': child.location.to_deprecated_string(),
                                })

                        problem = {
                            'xValue': label,
                            'stackData': stack_data,
                        }
                        data.append(problem)
        curr_section['data'] = data

        d3_data.append(curr_section)

    return d3_data


def get_d3_sequential_open_distrib(course_id):
    """
    Returns how many students opened a sequential/subsection for each section, data already in format for d3 function.

    `course_id` the course ID for the course interested in

    Returns an array in the order of the sections and each dict has:
      'display_name' - display name for the section
      'data' - data for the d3_stacked_bar_graph function of how many students opened each sequential/subsection
    """
    sequential_open_distrib = get_sequential_open_distrib(course_id)

    d3_data = []

    # Retrieve course object down to subsection
    course = modulestore().get_course(course_id, depth=2)

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

            num_students = 0
            if subsection.location.to_deprecated_string() in sequential_open_distrib:
                num_students = sequential_open_distrib[subsection.location.to_deprecated_string()]

            stack_data = []
            tooltip = _("{num_students} student(s) opened Subsection {subsection_num}: {subsection_name}").format(
                num_students=num_students,
                subsection_num=c_subsection,
                subsection_name=subsection_name,
            )

            stack_data.append({
                'color': 0,
                'value': num_students,
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


def get_d3_section_grade_distrib(course_id, section):
    """
    Returns the grade distribution for the problems in the `section` section in a format for the d3 code.

    `course_id` a string that is the course's ID.

    `section` an int that is a zero-based index into the course's list of sections.

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
                if (child.location.category == 'problem'):
                    c_problem += 1
                    problem_set.append(child.location)
                    problem_info[child.location] = {
                        'id': child.location.to_deprecated_string(),
                        'x_value': "P{0}.{1}.{2}".format(c_subsection, c_unit, c_problem),
                        'display_name': own_metadata(child).get('display_name', ''),
                    }

    # Retrieve grade distribution for these problems
    grade_distrib = get_problem_set_grade_distrib(course_id, problem_set)

    d3_data = []

    # Construct data for each problem to be sent to d3
    for problem in problem_set:
        stack_data = []

        if problem in grade_distrib:  # Some problems have no data because students have not tried them yet.
            max_grade = float(grade_distrib[problem]['max_grade'])
            for (grade, count_grade) in grade_distrib[problem]['grade_distrib']:
                percent = 0.0
                if max_grade > 0:
                    percent = (grade * 100.0) / max_grade

                # Construct tooltip for problem in grade distibution view
                tooltip = _("{problem_info_x} {problem_info_n} - {count_grade} {students} ({percent:.0f}%: {grade:.0f}/{max_grade:.0f} {questions})").format(
                    problem_info_x=problem_info[problem]['x_value'],
                    count_grade=count_grade,
                    students=_("students"),
                    percent=percent,
                    problem_info_n=problem_info[problem]['display_name'],
                    grade=grade,
                    max_grade=max_grade,
                    questions=_("questions"),
                )

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
                    if child.location.category == 'problem':
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
    module_id = Location.from_deprecated_string(request.GET.get('module_id'))
    csv = request.GET.get('csv')

    # Query for "opened a subsection" students
    students = models.StudentModule.objects.select_related('student').filter(
        module_id__exact=module_id,
        module_type__exact='sequential',
    ).values('student__username', 'student__profile__name').order_by('student__profile__name')

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
        filename = sanitize_filename(tooltip[tooltip.index('S'):])

        header = ['Name', 'Username']
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
    module_id = Location.from_deprecated_string(request.GET.get('module_id'))
    csv = request.GET.get('csv')

    # Query for "problem grades" students
    students = models.StudentModule.objects.select_related('student').filter(
        module_id__exact=module_id,
        module_type__exact='problem',
        grade__isnull=False,
    ).values('student__username', 'student__profile__name', 'grade', 'max_grade').order_by('student__profile__name')

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

        header = ['Name', 'Username', 'Grade', 'Percent']
        for student in students:

            percent = 0
            if student['max_grade'] > 0:
                percent = round(student['grade'] * 100 / student['max_grade'])
            results.append([student['student__profile__name'], student['student__username'], student['grade'], percent])

        response = create_csv_response(filename, header, results)
        return response


def sanitize_filename(filename):
    """
    Utility function
    """
    filename = filename.replace(" ", "_")
    filename = filename.encode('ascii')
    filename = filename[0:25] + '.csv'
    return filename
