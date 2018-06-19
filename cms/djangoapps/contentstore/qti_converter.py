#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module provides functionality for converting QTI tests into edx courses.
Code is written for QTI 1.2 (https://www.imsglobal.org/question/qtiv1p2/imsqti_asi_bindv1p2.html)
Supported types of problems are: essay_question, multiple_answers_question,
multiple_choice_question, matching_question and fill_in_multiple_blanks_question.
Other problem types will be ignored during conversion.
Converter looks for imsmanifest.xml in root directory of archive and parses all the resources (xml
files) listed in there. As a result it creates a .tar.gz archive suitable for import in existing
course.
"""

from shutil import copyfile
import datetime
import xml.etree.ElementTree as ET
from collections import OrderedDict
import os
import re
import uuid

NS = {'qti': 'http://www.imsglobal.org/xsd/ims_qtiasiv1p2',
      'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
      'schemaLocation': 'http://www.imsglobal.org/xsd/ims_qtiasiv1p2',
      'ims': 'http://www.imsglobal.org/xsd/imsccv1p1/imscp_v1p1',
      'meta': 'http://canvas.instructure.com/xsd/cccv1p0'}


class Course(object):
    """
    Class representing one course
    """

    def __init__(self):
        self.assessments = []


class Item(object):
    """
    Class representing one problem
    """

    def __init__(self):
        self.title = ''
        self.metafields = {}
        self.mattext = ''
        self.responses = {}
        self.feedback = {}
        self.correct = []
        self.match = OrderedDict()
        self.match_correct = {}


class Assessment(object):
    """
    Class representing one section
    """

    def __init__(self):
        self.ident = ''
        self.title = ''
        self.items = []
        self.description = ''
        self.start = ''
        self.end = ''
        self.show_correct = ''
        self.show_correct_at_end = ''
        self.allowed_attempts = '1'
        self.time_limit = ''


def parse_meta(element, subject):
    """
    Parse metadata of QTI element
    """
    meta = element.find('qti:qtimetadata', NS)
    if meta is not None:
        for metadatafield in meta.findall('qti:qtimetadatafield', NS):
            metalabel = metadatafield.find('qti:fieldlabel', NS).text
            metavalue = metadatafield.find('qti:fieldentry', NS).text
            subject.metafields.update({metalabel: metavalue})


def get_mattext(element):
    """
    Get text from material QTI xml element.
    """
    material = element.find('qti:material', NS)
    if material is not None:
        temp_str = material.find('qti:mattext', NS).text
        # Update img tag to match new location of images
        temp_str = re.sub(r'src="(?:[^"/]*/)*([^"]+)"', r'src="/static/\1"', temp_str)
        # Add closing tag for br and img elements
        temp_str = re.sub(r'(<img("[^"]*"|[^/">])*)>', r'\1/>', temp_str)
        temp_str = re.sub('<br.*?>', '<br/>', temp_str)
        return temp_str
    return ''


def text_from_html(temp_str):
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
    for assessment_el in root.findall('qti:assessment', NS):
        new_assessment.title = assessment_el.get('title').replace('&', 'and')
        new_assessment.ident = assessment_el.get('ident')
        for item_el in tree.findall('.//qti:section[1]//qti:item', NS):
            new_item = Item()
            new_item.title = item_el.get('title').replace('&', 'and')
            parse_meta(item_el.find('qti:itemmetadata', NS), new_item)

            presentation = item_el.find('qti:presentation', NS)
            new_item.mattext = get_mattext(presentation)
            for response_element in presentation.findall('qti:response_lid', NS):
                match_text = get_mattext(response_element)
                if match_text:
                    new_item.match.update({match_text: response_element.get('ident')})
                for response in response_element.find('qti:render_choice', NS). \
                        findall('qti:response_label', NS):
                    response_id = response.get('ident')
                    value = get_mattext(response)
                    new_item.responses.update({response_id: value})

            resprocessing = item_el.find('qti:resprocessing', NS)
            for respcondition_el in resprocessing.findall('qti:respcondition', NS):
                if respcondition_el.find('qti:setvar', NS) is not None:
                    conditionvar = respcondition_el.find('qti:conditionvar', NS)
                    condition = conditionvar.find('qti:and', NS)
                    if condition is None:
                        condition = conditionvar
                    for answer in condition.findall('qti:varequal', NS):
                        new_item.correct.extend([answer.text])
                        new_item.match_correct.update({answer.get('respident'): answer.text})

            for feedback_element in item_el.findall('qti:itemfeedback', NS):
                flowmat = feedback_element.find('qti:flow_mat', NS)
                value = get_mattext(flowmat)
                new_item.feedback.update({feedback_element.get('ident'): value})

            new_assessment.items.extend([new_item])


def write_essay_question(item, vertical_root, chapter):
    """
    Write essay question to file.
    """
    open_ass_el = ET.SubElement(vertical_root, 'openassessment')
    open_ass_el.set("url_name", uuid.uuid3(uuid.NAMESPACE_DNS, item.mattext.encode('utf-8')).hex)
    open_ass_el.set("submission_start", chapter.start)
    open_ass_el.set("submission_due", chapter.end)
    open_ass_el.set("text_response", "required")
    open_ass_el.set("allow_latext", "False")
    title_el = ET.SubElement(open_ass_el, 'title')
    title_el.text = item.title
    asss_el = ET.SubElement(open_ass_el, 'assessments')
    ass_el = ET.SubElement(asss_el, 'assessment')
    ass_el.set("name", "staff-assessment")
    ass_el.set("required", "True")
    prompts_el = ET.SubElement(open_ass_el, 'prompts')
    prompt_el = ET.SubElement(prompts_el, 'prompt')
    desc_el = ET.SubElement(prompt_el, 'description')
    desc_el.text = text_from_html(item.mattext)
    rubric_el = ET.SubElement(open_ass_el, 'rubric')
    criterion_el = ET.SubElement(rubric_el, 'criterion')
    criterion_el.set("feedback", "required")
    name_el = ET.SubElement(criterion_el, 'name')
    name_el.text = "0"
    lab_el = ET.SubElement(criterion_el, 'label')
    lab_el.text = "Criteria"
    prom_el = ET.SubElement(criterion_el, 'prompt')
    prom_el.text = "Is the answer correct?"
    feedback_prom_el = ET.SubElement(rubric_el, 'feedbackprompt')
    feedback_prom_el.text = 'What aspects of this response stood out to you? What did it do well? '\
                            'How could it be improved? '
    feedback_def_el = ET.SubElement(rubric_el, 'feedback_default_text')
    feedback_def_el.text = 'I think that this response...'


def write_multiple_answers_question(item, problem_root):
    """
    Write multiple answers question to file.
    """
    choice_resp_el = ET.SubElement(problem_root, 'choiceresponse')
    p_el = ET.SubElement(choice_resp_el, 'p')
    p_el.text = item.mattext
    label = ET.SubElement(choice_resp_el, 'label')
    choice_group_el = ET.SubElement(choice_resp_el, 'checkboxgroup')
    for number, answer in item.responses.items():
        choice_el = ET.SubElement(choice_group_el, 'choice')
        choice_el.set("correct", str(number in item.correct))
        choice_el.text = answer


def write_multiple_choice_question(item, problem_root):
    """
    Write multiple choice question to file.
    """
    multi_choice_el = ET.SubElement(problem_root, 'multiplechoiceresponse')
    p_el = ET.SubElement(multi_choice_el, 'p')
    p_el.text = item.mattext
    choice_group_el = ET.SubElement(multi_choice_el, 'choicegroup')
    choice_group_el.set("type", "MultipleChoice")
    for number, answer in item.responses.items():
        choice_el = ET.SubElement(choice_group_el, 'choice')
        choice_el.set("correct", str(number in item.correct))
        choice_el.text = answer
        feedback_name = 'general_incorrect_fb'
        if number in item.correct:
            feedback_name = 'correct_fb'
        if feedback_name in item.feedback:
            choice_hint_el = ET.SubElement(choice_el, 'choicehint')
            choice_hint_el.text = item.feedback[feedback_name]


def write_fill_in_multiple_blanks_question(item, problem_root):
    """
    Write fill in multiple blanks question to file.
    """
    num_resp_el = ET.SubElement(problem_root, 'numericalresponse')
    num_resp_el.set("answer", item.responses[item.correct[0]])
    p_el = ET.SubElement(num_resp_el, 'p')
    p_el.text = item.mattext
    label = ET.SubElement(num_resp_el, 'label')
    f_eq_el = ET.SubElement(num_resp_el, 'formulaequationinput')


def write_matching_question(item, problem_root):
    """
    Write matching question to file.
    """
    option_response_el = ET.SubElement(problem_root, 'optionresponse')
    p_el = ET.SubElement(option_response_el, 'p')
    p_el.text = item.mattext
    for match_text, match_id in item.match.items():
        desc_el = ET.SubElement(option_response_el, 'description')
        desc_el.text = match_text
        option_input_el = ET.SubElement(option_response_el, 'optioninput')
        for number, answer in item.responses.items():
            is_correct = number == item.match_correct[match_id]
            option_el = ET.SubElement(option_input_el, 'option')
            option_el.set("correct", str(is_correct))
            option_el.text = answer


def write_problem(item, vertical_root, chapter, problem_dir):
    """
    Write one problem to disk.
    """
    if item.metafields['question_type'] == 'essay_question':
        write_essay_question(item, vertical_root, chapter)
        return

    item_id = item.metafields['assessment_question_identifierref']

    problem_root = ET.Element('problem')
    problem_root.set("max_attempts", chapter.allowedAttempts)
    problem_root.set("display_name", item.title)
    problem_root.set("weight", "1.0")
    if item.metafields['question_type'] == 'multiple_answers_question':
        write_multiple_answers_question(item, problem_root)
    elif item.metafields['question_type'] == 'multiple_choice_question':
        write_multiple_choice_question(item, problem_root)
    elif item.metafields['question_type'] == 'fill_in_multiple_blanks_question':
        write_fill_in_multiple_blanks_question(item, problem_root)
    elif item.metafields['question_type'] == 'matching_question':
        write_matching_question(item, problem_root)

    problem_el = ET.SubElement(vertical_root, 'problem')
    problem_el.set("url_name", item_id)

    problem_f = open('{0}/{1}.xml'.format(problem_dir, item_id), "w+")
    problem_f.write(ET.tostring(problem_root).replace('&amp;', '&').replace('&gt;', '>')
                    .replace('&lt;', '<'))
    problem_f.close()


def write_chapter(chapter, html_dir, course_root, chapter_dir, seq_dir, vertical_dir, problem_dir):
    """
    Write one chapter to disk.
    """
    if not chapter.items:
        return

    html_id = uuid.uuid3(uuid.NAMESPACE_DNS, chapter.description).hex
    if chapter.description:
        html_f = open('{0}/{1}.html'.format(html_dir, html_id), 'w+')
        html_xml = open('{0}/{1}.xml'.format(html_dir, html_id), 'w+')
        html_xml.write('<html filename="{0}"/>'.format(html_id))
        html_f.write('<p>{0}</p>'.format(chapter.description))
        html_f.close()
        html_xml.close()

    chapter_el = ET.SubElement(course_root, 'chapter')
    chapter_el.set("url_name", chapter.ident)

    chapter_root = ET.Element('chapter')
    chapter_root.set("display_name", chapter.title)
    sequential_el = ET.SubElement(chapter_root, 'sequential')
    sequential_el.set("url_name", chapter.ident)
    chapter_f = open('{0}/{1}.xml'.format(chapter_dir, chapter.ident), 'w+')
    chapter_f.write(ET.tostring(chapter_root))
    chapter_f.close()

    sequential_root = ET.Element('sequential')
    sequential_root.set("display_name", "Subsection")
    sequential_root.set("due", chapter.end)
    sequential_root.set("start", chapter.start)
    sequential_root.set("show_correctness", "always")
    if chapter.time_limit:
        sequential_root.set("is_time_limited", "true")
        sequential_root.set("is_proctored_enabled", "false")
        sequential_root.set("is_practice_exam", "false")
        sequential_root.set("default_time_limit_minutes", chapter.time_limit)
    vertical_el = ET.SubElement(sequential_root, 'vertical')
    vertical_el.set("url_name", chapter.ident)
    seq_f = open('{0}/{1}.xml'.format(seq_dir, chapter.ident), 'w+')
    seq_f.write(ET.tostring(sequential_root))
    seq_f.close()

    vertical_root = ET.Element('vertical')
    vertical_root.set("display_name", chapter.title)

    if chapter.description:
        html_el = ET.SubElement(vertical_root, 'html')
        html_el.set("url_name", html_id)
    for item in chapter.items:
        write_problem(item, vertical_root, chapter, problem_dir)

    vertical_f = open('{0}/{1}.xml'.format(vertical_dir, chapter.ident), "w+")
    vertical_f.write(ET.tostring(vertical_root).replace('&amp;', '&').replace('&gt;', '>')
                     .replace('&lt;', '<'))
    vertical_f.close()


def write_olx(course_directory, course):
    """
    Write parsed OLX file data to file system.
    """
    course_el = ET.Element('course')
    course_el.set("url_name", "course")
    course_el.set("org", "credo")
    course_el.set("course", "csl")
    course_f = open('{0}/course.xml'.format(course_directory), 'w+')
    course_f.write(ET.tostring(course_el))
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

    course_root = ET.Element('course')
    course_root.set("display_name", "Course")
    course_root.set("show_chat", "false")
    course_root.set("enable_timed_exams", "true")
    course_root.set("enable_proctored_exams", "false")

    for chapter in course.assessments:
        write_chapter(chapter, html_dir, course_root, chapter_dir, seq_dir, vertical_dir,
                      problem_dir)

    course_xml = open('{0}/course.xml'.format(course_dir), "w+")
    course_xml.write(ET.tostring(course_root))
    course_xml.close()


def parse_assessment_meta(assessment_meta_xml, new_assessment):
    """
    Parse metafile for one assessment.
    """
    meta_root = assessment_meta_xml.getroot()
    desc = meta_root.find('meta:description', NS).text
    if desc is not None:
        new_assessment.description = re.sub('&lt.*?&gt;|<.*?>|\n', '', desc.encode('utf-8'))

    end_time = meta_root.find('meta:due_at', NS)
    if end_time is not None:
        new_assessment.end = end_time.text
    else:
        end_time = meta_root.find('meta:lock_at', NS)
        if end_time is not None:
            new_assessment.end = end_time.text
    start_time = meta_root.find('meta:unlock_at', NS)
    if start_time is not None:
        new_assessment.start = start_time.text
    else:
        new_assessment.start = datetime.datetime.now().replace(microsecond=0).isoformat()
        new_assessment.end = (datetime.datetime.now() +
                              datetime.timedelta(days=7)).replace(microsecond=0).isoformat()

    max_attempts = meta_root.find('meta:allowed_attempts', NS)
    if max_attempts is not None:
        new_assessment.allowedAttempts = max_attempts.text
    time_limit = meta_root.find('meta:time_limit', NS)
    if time_limit is not None:
        new_assessment.time_limit = time_limit.text
    new_assessment.showCorrect = meta_root.find('meta:show_correct_answers', NS).text
    new_assessment.showCorrectAtEnd = meta_root.find('meta:show_correct_answers_last_attempt',
                                                     NS).text


def convert_to_olx(path_to_ims):
    """
    Convert folder with qti course into a folder with edx course.
    """
    manifest = '{0}imsmanifest.xml'.format(path_to_ims)
    quiz = Course()
    manifest_xml = ET.parse(manifest)
    root_manifest = manifest_xml.getroot()

    directory = path_to_ims
    if not os.path.exists(directory):
        os.makedirs(directory)

    for resource in root_manifest.find('ims:resources', NS).findall('ims:resource', NS):
        if resource.get('type') == "webcontent":
            static_directory = '{0}/static'.format(directory)
            if not os.path.exists(static_directory):
                os.makedirs(static_directory)
            image_file = '{0}{1}'.format(path_to_ims, resource.get('href'))
            new_image_file = '{0}/{1}'.format(static_directory,
                                              os.path.basename(resource.get('href')))
            copyfile(image_file, new_image_file)

        if resource.get('type') == "imsqti_xmlv1p2":
            xmlfile = resource.find('ims:file', NS)
            xml = ET.parse(path_to_ims + xmlfile.get('href'))
            new_assessment = Assessment()
            parse_assessment(xml, new_assessment)
            assessment_meta_xml = ET.parse(
                path_to_ims + resource.get('identifier') + '/assessment_meta.xml')
            parse_assessment_meta(assessment_meta_xml, new_assessment)
            quiz.assessments.extend([new_assessment])

    write_olx(directory, quiz)
