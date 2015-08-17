import logging
from lxml import etree

log = logging.getLogger(__name__)

GRADER_TYPE_IMAGE_DICT = {
    'SA': '/static/images/self_assessment_icon.png',
    'PE': '/static/images/peer_grading_icon.png',
    'ML': '/static/images/ml_grading_icon.png',
    'IN': '/static/images/peer_grading_icon.png',
    'BC': '/static/images/ml_grading_icon.png',
}

_ = lambda text: text

HUMAN_GRADER_TYPE = {
    # Translators: "Self-Assessment" refers to the self-assessed mode of openended evaluation
    'SA': _('Self-Assessment'),
    # Translators: "Peer-Assessment" refers to the peer-assessed mode of openended evaluation
    'PE': _('Peer-Assessment'),
    # Translators: "Instructor-Assessment" refers to the instructor-assessed mode of openended evaluation
    'IN': _('Instructor-Assessment'),
    # Translators: "AI-Assessment" refers to the machine-graded mode of openended evaluation
    'ML': _('AI-Assessment'),
    # Translators: "AI-Assessment" refers to the machine-graded mode of openended evaluation
    'BC': _('AI-Assessment'),
}

DO_NOT_DISPLAY = ['BC', 'IN']

LEGEND_LIST = [{'name': HUMAN_GRADER_TYPE[k], 'image': GRADER_TYPE_IMAGE_DICT[k]} for k in GRADER_TYPE_IMAGE_DICT.keys()
               if k not in DO_NOT_DISPLAY]


class RubricParsingError(Exception):
    def __init__(self, msg):
        self.msg = msg


class CombinedOpenEndedRubric(object):
    TEMPLATE_DIR = "combinedopenended/openended"

    def __init__(self, render_template, view_only=False):
        self.has_score = False
        self.view_only = view_only
        self.render_template = render_template

    def render_rubric(self, rubric_xml, score_list=None):
        '''
        render_rubric: takes in an xml string and outputs the corresponding
            html for that xml, given the type of rubric we're generating
        Input:
            rubric_xml: an string that has not been parsed into xml that
                represents this particular rubric
        Output:
            html: the html that corresponds to the xml given
        '''
        success = False
        try:
            rubric_categories = self.extract_categories(rubric_xml)
            if score_list and len(score_list) == len(rubric_categories):
                for i in xrange(len(rubric_categories)):
                    category = rubric_categories[i]
                    for j in xrange(len(category['options'])):
                        if score_list[i] == j:
                            rubric_categories[i]['options'][j]['selected'] = True
            rubric_scores = [cat['score'] for cat in rubric_categories]
            max_scores = map((lambda cat: cat['options'][-1]['points']), rubric_categories)
            max_score = max(max_scores)
            rubric_template = '{0}/open_ended_rubric.html'.format(self.TEMPLATE_DIR)
            if self.view_only:
                rubric_template = '{0}/open_ended_view_only_rubric.html'.format(self.TEMPLATE_DIR)
            html = self.render_template(
                rubric_template,
                {
                    'categories': rubric_categories,
                    'has_score': self.has_score,
                    'view_only': self.view_only,
                    'max_score': max_score,
                    'combined_rubric': False,
                }
            )
            success = True
        except:
            #This is a staff_facing_error
            error_message = "[render_rubric] Could not parse the rubric with xml: {0}. Contact the learning sciences group for assistance.".format(
                rubric_xml)
            log.exception(error_message)
            raise RubricParsingError(error_message)
        return {'success': success, 'html': html, 'rubric_scores': rubric_scores}

    def check_if_rubric_is_parseable(self, rubric_string, location, max_score_allowed):
        rubric_dict = self.render_rubric(rubric_string)
        success = rubric_dict['success']
        rubric_feedback = rubric_dict['html']
        if not success:
            #This is a staff_facing_error
            error_message = "Could not parse rubric : {0} for location {1}. Contact the learning sciences group for assistance.".format(
                rubric_string, location.to_deprecated_string())
            log.error(error_message)
            raise RubricParsingError(error_message)

        rubric_categories = self.extract_categories(rubric_string)
        total = 0
        for category in rubric_categories:
            total = total + len(category['options']) - 1
            if len(category['options']) > (max_score_allowed + 1):
                #This is a staff_facing_error
                error_message = "Number of score points in rubric {0} higher than the max allowed, which is {1}. Contact the learning sciences group for assistance.".format(
                    len(category['options']), max_score_allowed)
                log.error(error_message)
                raise RubricParsingError(error_message)

        return int(total)

    def extract_categories(self, element):
        '''
        Contstruct a list of categories such that the structure looks like:
        [ { category: "Category 1 Name",
            options: [{text: "Option 1 Name", points: 0}, {text:"Option 2 Name", points: 5}]
            },
           { category: "Category 2 Name",
             options: [{text: "Option 1 Name", points: 0},
                         {text: "Option 2 Name", points: 1},
                         {text: "Option 3 Name", points: 2]}]

        '''
        if isinstance(element, basestring):
            element = etree.fromstring(element)
        categories = []
        for category in element:
            if category.tag != 'category':
                #This is a staff_facing_error
                raise RubricParsingError(
                    "[extract_categories] Expected a <category> tag: got {0} instead. Contact the learning sciences group for assistance.".format(
                        category.tag))
            else:
                categories.append(self.extract_category(category))
        return categories

    def extract_category(self, category):
        '''
        construct an individual category
        {category: "Category 1 Name",
         options: [{text: "Option 1 text", points: 1},
                   {text: "Option 2 text", points: 2}]}

        all sorting and auto-point generation occurs in this function
        '''
        descriptionxml = category[0]
        optionsxml = category[1:]
        scorexml = category[1]
        score = None
        if scorexml.tag == 'score':
            score_text = scorexml.text
            optionsxml = category[2:]
            score = int(score_text)
            self.has_score = True
        # if we are missing the score tag and we are expecting one
        elif self.has_score:
            #This is a staff_facing_error
            raise RubricParsingError(
                "[extract_category] Category {0} is missing a score. Contact the learning sciences group for assistance.".format(
                    descriptionxml.text))

        # parse description
        if descriptionxml.tag != 'description':
            #This is a staff_facing_error
            raise RubricParsingError(
                "[extract_category]: expected description tag, got {0} instead. Contact the learning sciences group for assistance.".format(
                    descriptionxml.tag))

        description = descriptionxml.text

        cur_points = 0
        options = []
        autonumbering = True
        # parse options
        for option in optionsxml:
            if option.tag != 'option':
                #This is a staff_facing_error
                raise RubricParsingError(
                    "[extract_category]: expected option tag, got {0} instead. Contact the learning sciences group for assistance.".format(
                        option.tag))
            else:
                pointstr = option.get("points")
                if pointstr:
                    autonumbering = False
                    # try to parse this into an int
                    try:
                        points = int(pointstr)
                    except ValueError:
                        #This is a staff_facing_error
                        raise RubricParsingError(
                            "[extract_category]: expected points to have int, got {0} instead. Contact the learning sciences group for assistance.".format(
                                pointstr))
                elif autonumbering:
                    # use the generated one if we're in the right mode
                    points = cur_points
                    cur_points = cur_points + 1
                else:
                    raise Exception(
                        "[extract_category]: missing points attribute. Cannot continue to auto-create points values after a points value is explicitly defined.")

                selected = score == points
                optiontext = option.text
                options.append({'text': option.text, 'points': points, 'selected': selected})

        # sort and check for duplicates
        options = sorted(options, key=lambda option: option['points'])
        CombinedOpenEndedRubric.validate_options(options)

        return {'description': description, 'options': options, 'score': score}

    def render_combined_rubric(self, rubric_xml, scores, score_types, feedback_types):
        success, score_tuples = CombinedOpenEndedRubric.reformat_scores_for_rendering(scores, score_types,
                                                                                      feedback_types)
        #Get all the categories in the rubric
        rubric_categories = self.extract_categories(rubric_xml)
        #Get a list of max scores, each entry belonging to a rubric category
        max_scores = map((lambda cat: cat['options'][-1]['points']), rubric_categories)
        actual_scores = []
        #Get the highest possible score across all categories
        max_score = max(max_scores)
        #Loop through each category
        for i, category in enumerate(rubric_categories):
            #Loop through each option in the category
            for j in xrange(len(category['options'])):
                #Intialize empty grader types list
                rubric_categories[i]['options'][j]['grader_types'] = []
                #Score tuples are a flat data structure with (category, option, grader_type_list) for selected graders
                for tup in score_tuples:
                    if tup[1] == i and tup[2] == j:
                        for grader_type in tup[3]:
                            #Set the rubric grader type to the tuple grader types
                            rubric_categories[i]['options'][j]['grader_types'].append(grader_type)
                            #Grab the score and add it to the actual scores.  J will be the score for the selected
                            #grader type
                            if len(actual_scores) <= i:
                                #Initialize a new list in the list of lists
                                actual_scores.append([j])
                            else:
                                #If a list in the list of lists for this position exists, append to it
                                actual_scores[i] += [j]

        actual_scores = [sum(i) / len(i) for i in actual_scores]
        correct = []
        #Define if the student is "correct" (1) "incorrect" (0) or "partially correct" (.5)
        for (i, a) in enumerate(actual_scores):
            if int(a) == max_scores[i]:
                correct.append(1)
            elif int(a) == 0:
                correct.append(0)
            else:
                correct.append(.5)

        html = self.render_template(
            '{0}/open_ended_combined_rubric.html'.format(self.TEMPLATE_DIR),
            {
                'categories': rubric_categories,
                'max_scores': max_scores,
                'correct': correct,
                'has_score': True,
                'view_only': True,
                'max_score': max_score,
                'combined_rubric': True,
                'grader_type_image_dict': GRADER_TYPE_IMAGE_DICT,
                'human_grader_types': HUMAN_GRADER_TYPE,
            }
        )
        return html

    @staticmethod
    def validate_options(options):
        '''
        Validates a set of options. This can and should be extended to filter out other bad edge cases
        '''
        if len(options) == 0:
            #This is a staff_facing_error
            raise RubricParsingError(
                "[extract_category]: no options associated with this category. Contact the learning sciences group for assistance.")
        if len(options) == 1:
            return
        prev = options[0]['points']
        for option in options[1:]:
            if prev == option['points']:
                #This is a staff_facing_error
                raise RubricParsingError(
                    "[extract_category]: found duplicate point values between two different options. Contact the learning sciences group for assistance.")
            else:
                prev = option['points']

    @staticmethod
    def reformat_scores_for_rendering(scores, score_types, feedback_types):
        """
        Takes in a list of rubric scores, the types of those scores, and feedback associated with them
        Outputs a reformatted list of score tuples (count, rubric category, rubric score, [graders that gave this score], [feedback types])
        @param scores:
        @param score_types:
        @param feedback_types:
        @return:
        """
        success = False
        if len(scores) == 0:
            #This is a dev_facing_error
            log.error("Score length is 0 when trying to reformat rubric scores for rendering.")
            return success, ""

        if len(scores) != len(score_types) or len(feedback_types) != len(scores):
            #This is a dev_facing_error
            log.error("Length mismatches when trying to reformat rubric scores for rendering.  "
                      "Scores: {0}, Score Types: {1} Feedback Types: {2}".format(scores, score_types, feedback_types))
            return success, ""

        score_lists = []
        score_type_list = []
        feedback_type_list = []
        for i in xrange(len(scores)):
            score_cont_list = scores[i]
            for j in xrange(len(score_cont_list)):
                score_list = score_cont_list[j]
                score_lists.append(score_list)
                score_type_list.append(score_types[i][j])
                feedback_type_list.append(feedback_types[i][j])

        score_list_len = len(score_lists[0])
        for score_list in score_lists:
            if len(score_list) != score_list_len:
                return success, ""

        score_tuples = []
        for i in xrange(len(score_lists)):
            for j in xrange(len(score_lists[i])):
                tuple = [1, j, score_lists[i][j], [], []]
                score_tuples, tup_ind = CombinedOpenEndedRubric.check_for_tuple_matches(score_tuples, tuple)
                score_tuples[tup_ind][0] += 1
                score_tuples[tup_ind][3].append(score_type_list[i])
                score_tuples[tup_ind][4].append(feedback_type_list[i])

        success = True
        return success, score_tuples

    @staticmethod
    def check_for_tuple_matches(tuples, tuple):
        """
        Checks to see if a tuple in a list of tuples is a match for tuple.
        If not match, creates a new tuple matching tuple.
        @param tuples: list of tuples
        @param tuple: tuples to match
        @return: a new list of tuples, and the index of the tuple that matches tuple
        """
        category = tuple[1]
        score = tuple[2]
        tup_ind = -1
        for ind in xrange(len(tuples)):
            if tuples[ind][1] == category and tuples[ind][2] == score:
                tup_ind = ind
                break

        if tup_ind == -1:
            tuples.append([0, category, score, [], []])
            tup_ind = len(tuples) - 1
        return tuples, tup_ind
