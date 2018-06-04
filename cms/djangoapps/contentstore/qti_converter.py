#! /usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import os
import re
import uuid
from shutil import copyfile
import ntpath
import datetime
from collections import OrderedDict

ns = {'qti': 'http://www.imsglobal.org/xsd/ims_qtiasiv1p2',
      'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
      'schemaLocation': 'http://www.imsglobal.org/xsd/ims_qtiasiv1p2',
      'ims': 'http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1',
      'meta': 'http://canvas.instructure.com/xsd/cccv1p0'}


class Quiz(object):
    def __init__(self):
        self.assessments = []


class Item(object):
    def __init__(self):
        self.title = ''
        self.metafields = {}
        self.mattext = ''
        self.responses = {}
        self.score = 100
        self.feedback = {}
        self.correct = []
        self.match = OrderedDict()
        self.matchCorrect = {}


class Assessment(object):
    def __init__(self):
        self.title = ''
        self.items = []
        self.metafields = {}
        self.description = ''
        self.start = ''
        self.end = ''
        self.showCorrect = ''
        self.showCorrectAtEnd = ''
        self.allowedAttempts = '1'
        self.timeLimit = ''


def parse_meta(element, subject):
    """
    Parse metadata of QTI element
    """
    meta = element.find('qti:qtimetadata', ns)
    if meta is not None:
        for metadatafield in meta.findall('qti:qtimetadatafield', ns):
            metalabel = metadatafield.find('qti:fieldlabel', ns).text
            metavalue = metadatafield.find('qti:fieldentry', ns).text
            subject.metafields.update({metalabel: metavalue})


def get_mattext(element):
    """
    Get text from material QTI xml element.
    """
    material = element.find('qti:material', ns)
    if material is not None:
        temp_str = material.find('qti:mattext', ns).text
        temp_str = re.sub(r'src="(?:[^"/]*/)*([^"]+)"', r'src="/static/\1"', temp_str)
        temp_str = re.sub(r'(<img("[^"]*"|[^/">])*)>', r'\1/>', temp_str)
        temp_str = re.sub('<br.*?>', '<br/>', temp_str)
        return temp_str.encode('utf-8')
    return ''


def text_from_htlm(temp_str):
    """
    Remove tags from string.
    """
    temp_str = temp_str.replace('<br/>', '\n')
    temp_str = re.sub('<[^>]*>', '', temp_str)
    return temp_str


def parse_assessment(tree, new_assessment):
    """
    Parse one QTI assessment file.
    """
    root = tree.getroot()
    i = 1
    for assessment in root.findall('qti:assessment', ns):
        new_assessment.title = assessment.get('title').replace('&', 'and')
        parse_meta(assessment, new_assessment)
        for item in tree.findall('.//qti:section[' + str(i) + ']//qti:item', ns):
            new_item = Item()
            new_item.title = item.get('title').replace('&', 'and')
            parse_meta(item.find('qti:itemmetadata', ns), new_item)

            presentation = item.find('qti:presentation', ns)
            new_item.mattext = get_mattext(presentation)
            for responseElement in presentation.findall('qti:response_lid', ns):
                match_text = get_mattext(responseElement)
                if match_text:
                    new_item.match.update({match_text: responseElement.get('ident')})
                for response in responseElement.find('qti:render_choice', ns).findall('qti:response_label', ns):
                    response_id = response.get('ident')
                    value = get_mattext(response)
                    new_item.responses.update({response_id: value})

            resprocessing = item.find('qti:resprocessing', ns)
            for respcondition in resprocessing.findall('qti:respcondition', ns):
                if respcondition.find('qti:setvar', ns) is not None:
                    conditionvar = respcondition.find('qti:conditionvar', ns)
                    condition = conditionvar.find('qti:and', ns)
                    if condition is None:
                        condition = conditionvar
                    for answer in condition.findall('qti:varequal', ns):
                        new_item.correct.extend([answer.text])
                        new_item.matchCorrect.update({answer.get('respident'): answer.text})

            for feedbackElement in item.findall('qti:itemfeedback', ns):
                flowmat = feedbackElement.find('qti:flow_mat', ns)
                value = get_mattext(flowmat)
                new_item.feedback.update({feedbackElement.get('ident'): value})

            new_assessment.items.extend([new_item])


def write_olx(course_directory, course):
    """
    Write parsed OLX file data to file system.
    """
    course_f = open('{0}/course.xml'.format(course_directory), 'w+')
    course_f.write("<course url_name=\"course\" org=\"credo\" course=\"cs1\"/>")
    course_f.close()

    chapter_dir = '{0}/chapter'.format(course_directory)
    os.makedirs(chapter_dir)
    course_dir = '{0}/course'.format(course_directory)
    os.makedirs(course_dir)
    problem_dir = '{0}/problem'.format(course_directory)
    os.makedirs(problem_dir)
    seq_dir = '{0}/sequential'.format(course_directory)
    os.makedirs(seq_dir)
    vertical_dir = '{0}/vertical'.format(course_directory)
    os.makedirs(vertical_dir)
    html_dir = '{0}/html'.format(course_directory)
    os.makedirs(html_dir)

    course_xml = open('{0}/course.xml'.format(course_dir), "w+")
    course_xml.write('<course display_name="Course" show_chat="false" enable_timed_exams="true" '
                     'enable_proctored_exams="false">')

    for chapter in course.assessments:
        if not chapter.items:
            continue

        html_id = uuid.uuid4().hex
        if chapter.description:
            html_f = open('{0}/{1}.html'.format(html_dir, html_id), 'w+')
            html_xml = open('{0}/{1}.xml'.format(html_dir, html_id), 'w+')
            html_xml.write('<html filename="{0}"/>'.format(html_id))
            html_f.write('<p>{0}</p>'.format(chapter.description))
            html_f.close()
            html_xml.close()

        chapter_id = uuid.uuid4().hex
        course_xml.write('<chapter url_name="{0}"/>'.format(chapter_id))
        chapter_f = open('{0}/{1}.xml'.format(chapter_dir, chapter_id), 'w+')
        chapter_f.write('<chapter display_name="{0}">'.format(chapter.title))
        seq_id = uuid.uuid4().hex
        chapter_f.write('<sequential url_name="{0}"/>'.format(seq_id))
        seq_f = open('{0}/{1}.xml'.format(seq_dir, seq_id), 'w+')

        show_correct = 'never'
        if chapter.showCorrect == 'true':
            show_correct = 'always'
        elif chapter.showCorrectAtEnd == 'true':
            show_correct = 'past_due'
        show_correct = 'always'  # COMMENT OUT THIS LINE IF YOU WANT TO USE SETTINGS FROM ASSESSMENT_META

        seq_f.write('<sequential display_name="Subsection" due="{0}" start="{1}" show_correctness="{2}" '
                    .format(chapter.end, chapter.start, show_correct))
        if chapter.timeLimit:
            seq_f.write('is_time_limited="true" is_proctored_enabled="false" is_practice_exam="false" '
                        'default_time_limit_minutes="{0}"'.format(chapter.timeLimit))
        seq_f.write('>')

        vertical_id = uuid.uuid4().hex
        vertical_f = open('{0}/{1}.xml'.format(vertical_dir, vertical_id), "w+")
        vertical_f.write('<vertical display_name="{0}">'.format(chapter.title))
        if chapter.description:
            vertical_f.write('<html url_name="{0}"/>'.format(html_id))
        for item in chapter.items:
            if item.metafields['question_type'] == 'essay_question':
                vertical_f.write('<openassessment url_name="{0}" submission_start="{1}" submission_due="{2}" '
                                 'text_response="required" allow_latext="False">'.
                                 format(uuid.uuid4().hex, chapter.start.replace('&quot;', ''),
                                        chapter.end.replace('&quot;', '')))
                vertical_f.write('<title>{0}</title><assessments><assessment name="staff-assessment" '
                                 'required="True"/></assessments>'.format(item.title))
                vertical_f.write('<prompts><prompt><description>{0}</description></prompt></prompts>'.
                                 format(text_from_htlm(item.mattext)))
                vertical_f.write('<rubric><criterion feedback="required"><name>0</name><label>Criteria</label><prompt'
                                 '>Is the answer correct?</prompt></criterion><feedbackprompt>What aspects of this '
                                 'response stood out to you? What did it do well? How could it be '
                                 'improved?</feedbackprompt><feedback_default_text>I think that this '
                                 'response...</feedback_default_text></rubric></openassessment>')
                continue

            item_id = item.metafields['assessment_question_identifierref']
            problem_f = open('{0}/{1}.xml'.format(problem_dir, item_id), "w+")
            if item.metafields['question_type'] == 'multiple_answers_question':
                problem_f.write('<problem max_attempts="{0}" display_name="{1}"><choiceresponse>'
                                .format(chapter.allowedAttempts, item.title))
                problem_f.write('<p>{0}</p><label></label><checkboxgroup>'.format(item.mattext))
                for number, answer in item.responses.items():
                    problem_f.write('<choice correct="{0}">{1}</choice>'.format(str(number in item.correct), answer))
                problem_f.write('</checkboxgroup>')
                problem_f.write('<solution></solution></choiceresponse></problem>')
            elif item.metafields['question_type'] == 'multiple_choice_question':
                problem_f.write('<problem max_attempts="{0}" display_name="{1}"><multiplechoiceresponse>'
                                .format(chapter.allowedAttempts, item.title))
                problem_f.write('<p>{0}</p><label></label><choicegroup type="MultipleChoice">'.format(item.mattext))
                for number, answer in item.responses.items():
                    correct = number in item.correct
                    problem_f.write('<choice correct="{0}">{1}'.format(str(correct), answer))
                    feedback_name = 'general_incorrect_fb'
                    if correct:
                        feedback_name = 'correct_fb'
                    if feedback_name in item.feedback:
                        problem_f.write('<choicehint>{0}</choicehint>'.format(item.feedback[feedback_name]))
                    problem_f.write('</choice>')
                problem_f.write('</choicegroup>')
                problem_f.write('<solution></solution></multiplechoiceresponse></problem>')
            elif item.metafields['question_type'] == 'fill_in_multiple_blanks_question':
                problem_f.write('<problem max_attempts="{0}" display_name="{1}"><numericalresponse answer="{2}">'
                                .format(chapter.allowedAttempts, item.title, item.responses[item.correct[0]]))
                problem_f.write('<p>{0}</p><label></label><formulaequationinput/></numericalresponse></problem>'
                                .format(item.mattext))
            elif item.metafields['question_type'] == 'matching_question':
                problem_f.write('<problem max_attempts="{0}" display_name="{1}" weight="1.0">'.
                                format(chapter.allowedAttempts, item.title))
                problem_f.write('<optionresponse><p>{0}</p>'.format(item.mattext))
                for match_text, match_id in item.match.items():
                    problem_f.write('<description>{0}</description><optioninput>'.format(match_text))
                    for number, answer in item.responses.items():
                        is_correct = number == item.matchCorrect[match_id]
                        problem_f.write('<option correct="{0}">{1}</option>'.format(str(is_correct), answer))
                    problem_f.write('</optioninput>')
                problem_f.write('</optionresponse></problem>')

            vertical_f.write('<problem url_name="{0}"/>'.format(item_id))
            problem_f.close()

        vertical_f.write('</vertical>')
        vertical_f.close()
        seq_f.write('<vertical url_name="{0}"/>'.format(vertical_id))
        seq_f.write('</sequential>')
        seq_f.close()
        chapter_f.write('</chapter>')
        chapter_f.close()

    course_xml.write('</course>')
    course_xml.close()


def parse_assessment_meta(assessment_meta_xml, new_assessment):
    """
    Parse metafile for one assessment.
    """
    meta_root = assessment_meta_xml.getroot()
    desc = meta_root.find('meta:description', ns).text
    if desc is not None:
        new_assessment.description = re.sub('&lt.*?\&gt;|<.*?>|\n', '', desc.encode('utf-8'))

    end_time = meta_root.find('meta:due_at', ns)
    if end_time is not None:
        new_assessment.end = '&quot;{0}&quot;'.format(end_time.text)
    else:
        end_time = meta_root.find('meta:lock_at', ns)
        if end_time is not None:
            new_assessment.end = '&quot;{0}&quot;'.format(end_time.text)
    start_time = meta_root.find('meta:unlock_at', ns)
    if start_time is not None:
        new_assessment.start = '&quot;{0}&quot;'.format(start_time.text)
    else:
        new_assessment.start = '&quot;{0}&quot;'.format(
            datetime.datetime.now().replace(microsecond=0).isoformat())
        new_assessment.end = '&quot;{0}&quot;'.format((datetime.datetime.now() + datetime.timedelta(days=7)).
                                                      replace(microsecond=0).isoformat())

    max_attempts = meta_root.find('meta:allowed_attempts', ns)
    if max_attempts is not None:
        new_assessment.allowedAttempts = max_attempts.text
    time_limit = meta_root.find('meta:time_limit', ns)
    if time_limit is not None:
        new_assessment.timeLimit = time_limit.text
    new_assessment.showCorrect = meta_root.find('meta:show_correct_answers', ns).text
    new_assessment.showCorrectAtEnd = meta_root.find('meta:show_correct_answers_last_attempt', ns).text


def convert_to_olx(path_to_ims):
    """
    Convert one QTI assessment to OLX course.
    """
    manifest = '{0}imsmanifest.xml'.format(path_to_ims)
    quiz = Quiz()
    manifest_xml = ET.parse(manifest)
    root_manifest = manifest_xml.getroot()

    directory = path_to_ims
    if not os.path.exists(directory):
        os.makedirs(directory)

    for resource in root_manifest.find('ims:resources', ns).findall('ims:resource', ns):
        if resource.get('type') == "webcontent":
            static_directory = '{0}/static'.format(directory)
            if not os.path.exists(static_directory):
                os.makedirs(static_directory)
            image_file = '{0}{1}'.format(path_to_ims, resource.get('href'))
            new_image_file = '{0}/{1}'.format(static_directory, ntpath.basename(resource.get('href')))
            copyfile(image_file, new_image_file)

        if resource.get('type') == "imsqti_xmlv1p2":
            xmlfile = resource.find('ims:file', ns)
            xml = ET.parse(path_to_ims + xmlfile.get('href'))
            new_assessment = Assessment()
            parse_assessment(xml, new_assessment)
            assessment_meta_xml = ET.parse(path_to_ims + resource.get('identifier') + '/assessment_meta.xml')
            parse_assessment_meta(assessment_meta_xml, new_assessment)
            quiz.assessments.extend([new_assessment])

    write_olx(directory, quiz)
