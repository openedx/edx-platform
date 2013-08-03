# Computes the data needed to display on the Instructor Dashboard

import json
import time

from json import JSONEncoder
from courseware import grades, models
from courseware.courses import get_course_by_id
from django.db.models import Count
from queryable.models import StudentModuleExpand
from queryable.models import Log

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata


def get_problem_grade_distribution(course_id):
    """Returns the grade distribution per problem for the course

    Output is a dicts, where the key is the problem module_id and the value is a dict with:
    max_grade - max grade for this problem
    grade_distrib - array of tuples (<grade>,<count>).

    """

    # select module_id, grade, max_grade, count(*) as count from courseware_studentmodule where grade is not null and module_type = "problem" and module_id like "%<Course number>%" group by module_id, grade order by module_id, grade;
    db_query = models.StudentModule.objects.filter(course_id__exact=course_id, grade__isnull=False, module_type__exact="problem").values('module_state_key','grade','max_grade').annotate(count_grade=Count('grade'))

    prob_grade_distrib = {}
    for row in db_query:
        if row['module_state_key'] in prob_grade_distrib:
            prob_grade_distrib[row['module_state_key']]['grade_distrib'].append((row['grade'],row['count_grade']))
            if (prob_grade_distrib[row['module_state_key']]['max_grade'] != row['max_grade']) and (prob_grade_distrib[row['module_state_key']]['max_grade'] < row['max_grade']):
                prob_grade_distrib[row['module_state_key']]['max_grade'] = row['max_grade']
        else:
            prob_grade_distrib[row['module_state_key']] = {
                'max_grade' : row['max_grade'],
                'grade_distrib' : [(row['grade'],row['count_grade'])]
                }

    return prob_grade_distrib


def get_problem_attempt_distrib(course_id, max_attempts=10):
    """Returns the attempt (between 1-10+) distribution per problem for the course

    Output is a dicts, where the key is the problem module_id and the value is an array where the first index is
    the number of students that only attempted once, second is two times, etc. The 11th index is all students that
    attempted more than ten times.
    """

    db_query = StudentModuleExpand.objects.filter(course_id__exact=course_id, attempts__isnull=False, module_type__exact="problem").values('module_state_key','attempts').annotate(count_attempts=Count('attempts'))

    prob_attempts_distrib = {}
    for row in db_query:
        if row['module_state_key'] not in prob_attempts_distrib:
            prob_attempts_distrib[row['module_state_key']] = [0] * (max_attempts+1)

        if row['attempts'] > max_attempts:
            prob_attempts_distrib[row['module_state_key']][max_attempts] += row['count_attempts']
        else:
            prob_attempts_distrib[row['module_state_key']][row['attempts']-1] = row['count_attempts']

    return prob_attempts_distrib


def get_sequential_open_distrib(course_id):
    """
    Returns the number of students that opened each subsection/sequential of the course

    Outputs a dict mapping the module id to the number of students that have opened that subsection/sequential.
    """

    db_query = models.StudentModule.objects.filter(course_id__exact=course_id, module_type__exact="sequential").values('module_state_key').annotate(count_sequential=Count('module_state_key'))

    sequential_open_distrib = {}
    for row in db_query:
        sequential_open_distrib[row['module_state_key']] = row['count_sequential']

    return sequential_open_distrib

def get_last_populate(course_id, script_id):
    """
    Returns the timestamp when a script was last run for a course.

    Returns None if there is no known time the script was last run for that course.
    """

    db_query = Log.objects.filter(course_id__exact=course_id, script_id__exact=script_id)

    if len(db_query) > 0:
        return db_query[0].created
    else:
        return None


def get_problem_set_grade_distribution(course_id, problem_set):
    """
    Returns the grade distribution for the problems specified in `problem_set`.

    Requests from the database the a count of each grade for each problem in the `problem_set`.

    `course_id` a string that is the course's ID.

    `problem_set` an array of strings representing problem module_id's.

    Returns a dict, where the key is the problem module_id and the value is a dict with two parts:
      `max_grade` - the maximum grade possible for the course
      `grade_distrib` - array of tuples (`grade`,`count`) ordered by `grade`
    """

    db_query = models.StudentModule.objects.filter(
        course_id__exact=course_id,
        grade__isnull=False,
        module_type__exact="problem",
        module_state_key__in=problem_set,
    ).values(
        'module_state_key',
        'grade',
        'max_grade'
    ).annotate(count_grade=Count('grade')).order_by('module_state_key','grade')

    prob_grade_distrib = {}
    for row in db_query:
        if row['module_state_key'] not in prob_grade_distrib:
            prob_grade_distrib[row['module_state_key']] = {
                'max_grade' : 0,
                'grade_distrib' : [],
            }

        curr_grade_distrib = prob_grade_distrib[row['module_state_key']]
        curr_grade_distrib['grade_distrib'].append((row['grade'],row['count_grade']))

        if curr_grade_distrib['max_grade'] < row['max_grade']:
            curr_grade_distrib['max_grade'] = row['max_grade']

    return prob_grade_distrib


def get_d3_problem_grade_distribution(course_id):
    prob_grade_distrib = get_problem_grade_distribution(course_id)

    # Get info on where each problem is
    course = modulestore().get_item(CourseDescriptor.id_to_location(course_id), depth=4)
    dict_id_to_display_names = {}
    cPosition = 0
    cSection = 0
    for section in course.get_children():
        cSection += 1
        sectionName = own_metadata(section)['display_name']
        cSubsection = 0
        for subsection in section.get_children():
            cSubsection += 1
            subsectionName = own_metadata(subsection)['display_name']
            cUnit = 0
            for unit in subsection.get_children():
                cUnit += 1
                unitName = own_metadata(unit)['display_name']
                cProblem = 0
                for child in unit.get_children():
                    if child.location.category == 'problem':
                        cProblem += 1
                        problemName = own_metadata(child)['display_name']
                        dict_id_to_display_names[child.location.url()] = {
                            'label': "{0}.{1}.{2}.{3}: {4}".format(cSection,cSubsection,cUnit,cProblem,problemName),
                            'detail': "{0}: {1}: {2}: {3}".format(sectionName, subsectionName, unitName, problemName),
                            'position': cPosition,
                            }
                        cPosition += 1
    
    d3_data = []

    for prob_id, value in prob_grade_distrib.iteritems():
        max_grade = float(value['max_grade'])
        
        label = "???"
        detail = "???"
        position = -1
        if prob_id in dict_id_to_display_names:
            detail = dict_id_to_display_names[prob_id]['detail']
            label = dict_id_to_display_names[prob_id]['label']
            position = dict_id_to_display_names[prob_id]['position']
        else:
            print "Can't find this id: ", prob_id
            
        stack_data = []
        for (grade,count_grade) in value['grade_distrib']:
            percent = 0.0
            if max_grade != 0:
                percent = (grade*100.0)/max_grade

            bar = {
                'color' : percent,
                'value' : count_grade,
                'tooltip' : "{0} - {1} students ({2:.0f}%:{3}/{4} questions)".format(detail, count_grade, 
                                                                                     percent, grade, max_grade),
                }
            stack_data.append(bar)

        stack = {
            'xValue' : label,
            'stackData' : stack_data,
            'position' : position
            }
        d3_data.append(stack)

    return sorted(d3_data, key=lambda stack: stack['position'])


def get_d3_problem_attempt_distribution(course_id, max_attempts=10):
    prob_attempts_distrib = get_problem_attempt_distrib(course_id, max_attempts)

    d3_data = []

    # Create an array of dicts. The ith element in the array maps to a section. Inside that is:
    #   - display_name - display name for the section
    #   - data - data for the attempt distribution of problems in this section for d3_stacked_bar_graph
    course = modulestore().get_item(CourseDescriptor.id_to_location(course_id), depth=4)
    c_section = 0
    for section in course.get_children():
        c_section += 1
        curr_section = {}
        curr_section['display_name'] = own_metadata(section)['display_name']
        data = []
        c_subsection = 0
        for subsection in section.get_children():
            c_subsection += 1
            c_unit = 0
            for unit in subsection.get_children():
                c_unit += 1
                c_problem = 0
                for child in unit.get_children():
                    if (child.location.category == 'problem'):
                        c_problem += 1
                        stack_data = []
                        label = "P{0}.{1}.{2}".format(c_subsection, c_unit, c_problem)
                        
                        if child.location.url() in prob_attempts_distrib:
                            attempts_distrib = prob_attempts_distrib[child.location.url()]
                            problem_name = own_metadata(child)['display_name']
                            for i in range(0, max_attempts+1):
                                color = (i+1 if i != max_attempts else "{0}+".format(max_attempts))
                                stack_data.append({
                                    'color' : color,
                                    'value' : attempts_distrib[i],
                                    'tooltip' : "{0} {3} - {1} Student(s) had {2} attempt(s)".format(
                                            label, attempts_distrib[i], color, problem_name),
                                })

                        problem = {
                            'xValue' : label,
                            'stackData' : stack_data,
                        }
                        data.append(problem)
        curr_section['data'] = data

        d3_data.append(curr_section)

    return d3_data


def get_d3_sequential_open_distribution(course_id):
    """
    Returns how many students opened a sequential/subsection for each section, data already in format for d3 function.

    Returns an array in the order of the sections and each dict has:
      'display_name' - display name for the section
      'data' - data for the d3 stacked bar graph function of how many students opened each sequential/subsection
    """
    sequential_open_distrib = get_sequential_open_distrib(course_id)

    d3_data = []

    course = modulestore().get_item(CourseDescriptor.id_to_location(course_id), depth=4)
    for section in course.get_children():
        curr_section = {}
        curr_section['display_name'] = own_metadata(section)['display_name']
        data = []
        c_subsection = 0
        for subsection in section.get_children():
            c_subsection += 1
            subsection_name = own_metadata(subsection)['display_name']

            num_students = 0
            if subsection.location.url() in sequential_open_distrib:
                num_students = sequential_open_distrib[subsection.location.url()]

            stack_data = []
            stack_data.append({
                    'color' : 0,
                    'value' : num_students,
                    'tooltip' : "{0} student(s) opened Subsection {1}: {2}".format(
                        num_students, c_subsection, subsection_name),
                    })
            subsection = {
                'xValue' : "SS {0}".format(c_subsection),
                'stackData' : stack_data,
                }
            data.append(subsection)

        curr_section['data'] = data
        d3_data.append(curr_section)

    return d3_data


def get_d3_problem_grade_distribution_by_section(course_id):
    """
    Returns problem grade distribution information for each section, data already in format for d3 function.

    Returns an array of dicts in the order of the sections. Each dict has:
      'display_name' - display name for the section
      'data' - data for the d3 stacked bar graph function of the grade distribution for that problem
    """

    prob_grade_distrib = get_problem_grade_distribution(course_id)
    d3_data = []

    course = modulestore().get_item(CourseDescriptor.id_to_location(course_id), depth=4)
    c_section = 0
    for section in course.get_children():
        c_section += 1
        curr_section = {}
        curr_section['display_name'] = own_metadata(section)['display_name']
        data = []
        c_subsection = 0
        for subsection in section.get_children():
            c_subsection += 1
            c_unit = 0
            for unit in subsection.get_children():
                c_unit += 1
                c_problem = 0
                for child in unit.get_children():
                    if (child.location.category == 'problem'):
                        c_problem += 1
                        stack_data = []
                        label = "P{0}.{1}.{2}".format(c_subsection, c_unit, c_problem)
                        
                        # Some problems have no data because students have not tried them yet
                        if child.location.url() in prob_grade_distrib:
                            problem_info = prob_grade_distrib[child.location.url()]
                            problem_name = own_metadata(child)['display_name']
                            max_grade = float(problem_info['max_grade'])
                            for (grade, count_grade) in problem_info['grade_distrib']:
                                percent = 0.0
                                if max_grade > 0:
                                    percent = (grade*100.0)/max_grade

                                stack_data.append({
                                    'color' : percent,
                                    'value' : count_grade,
                                    'tooltip' : "{0} {3} - {1} students ({2:.0f}%: {4:.0f}/{5:.0f} questions)".format(
                                            label, count_grade, percent, problem_name, grade, max_grade),
                                })
                                
                        problem = {
                            'xValue' : label,
                            'stackData' : stack_data,
                            }
                        data.append(problem)
        curr_section['data'] = data

        d3_data.append(curr_section)

    return d3_data


def get_d3_section_grade_distribution(course_id, section):
    """
    Returns the grade distribution for the problems in the `section` section in a format for the d3 code.

    Navigates the section specified to find all the problems associated with that section and then finds the grade
    distribution for those problems. Then returns an object formated the way the d3_stacked_bar_graph.js expects its
    data object to be in.

    `course_id` a string that is the course's ID.

    `section` an int that is a zero-based index into the course's list of sections.

    Returns an array of dicts with the following keys (taken from d3_stacked_bar_graph.js's documentation)
      `xValue` - Corresponding value for the x-axis
      `stackData` - Array of objects with key, value pairs that represent a bar:
        `color` - Defines what "color" the bar will map to
        `value` - Maps to the height of the bar, along the y-axis
        `tooltip` - (Optional) Text to display on mouse hover
    """

    course = modulestore().get_item(CourseDescriptor.id_to_location(course_id), depth=4)

    problem_set = []
    problem_info = {}
    c_subsection = 1
    for subsection in course.get_children()[section].get_children():
        c_unit = 1
        for unit in subsection.get_children():
            c_problem = 1
            for child in unit.get_children():
                if (child.location.category == 'problem'):
                    problem_set.append(child.location.url())
                    problem_info[child.location.url()] = {
                        'id' : child.location.url(),
                        'x_value' : "P{0}.{1}.{2}".format(c_subsection, c_unit, c_problem),
                        'display_name' : own_metadata(child)['display_name'],
                    }
                    c_problem+=1
            c_unit+=1
        c_subsection+=1

    grade_distrib = get_problem_set_grade_distribution(course_id, problem_set)

    d3_data = []
    for problem in problem_set:
        stack_data = []

        if problem in grade_distrib: # Some problems have no data because students have not tried them yet.
            max_grade = float(grade_distrib[problem]['max_grade'])
            for (grade, count_grade) in grade_distrib[problem]['grade_distrib']:
                percent = 0.0
                if max_grade > 0:
                    percent = (grade*100.0)/max_grade
                    stack_data.append({
                            'color' : percent,
                            'value' : count_grade,
                            'tooltip' : "{0} {3} - {1} students ({2:.0f}%: {4:.0f}/{5:.0f} questions)".format(
                                problem_info[problem]['x_value'],
                                count_grade,
                                percent,
                                problem_info[problem]['display_name'],
                                grade,
                                max_grade),
                            })
                    
        d3_data.append({
            'xValue' : problem_info[problem]['x_value'],
            'stackData' : stack_data,
        })

    return d3_data


def get_section_display_name(course_id):
    """
    Returns an array of the display names for each section in the course.

    The ith string in the array is the display name of the ith section in the course.
    """

    course = modulestore().get_item(CourseDescriptor.id_to_location(course_id), depth=4)

    section_display_name = [""] * len(course.get_children())
    i = 0
    for section in course.get_children():
        section_display_name[i] = own_metadata(section)['display_name']
        i+=1

    return section_display_name


def get_array_section_has_problem(course_id):
    """
    Returns an array of true/false whether each section has problems.

    The ith value in the array is true if the ith section in the course contains problems and false otherwise.
    """

    course = modulestore().get_item(CourseDescriptor.id_to_location(course_id), depth=4)

    b_section_has_problem = [False] * len(course.get_children())
    i = 0
    for section in course.get_children():
        for subsection in section.get_children():
            for unit in subsection.get_children():
                for child in unit.get_children():
                    if child.location.category == 'problem':
                        b_section_has_problem[i] = True
                        break # out of child loop
                if b_section_has_problem[i]:
                    break # out of unit loop
            if b_section_has_problem[i]:
                break # out of subsection loop

        i+=1

    return b_section_has_problem
