from mitxmako.shortcuts import render_to_string
import logging
from lxml import etree

log=logging.getLogger(__name__)

class CombinedOpenEndedRubric:

    @staticmethod
    def render_rubric(rubric_xml):
        try:
            rubric_categories = CombinedOpenEndedRubric.extract_rubric_categories(rubric_xml)
            html = render_to_string('open_ended_rubric.html', {'rubric_categories'  : rubric_categories})
        except:
            log.exception("Could not parse the rubric.")
            html = rubric_xml
        return html

    @staticmethod
    def extract_rubric_categories(element):
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
        element = etree.fromstring(element)
        categories = []
        for category in element:
            if category.tag != 'category':
                raise Exception("[capa.inputtypes.extract_categories] Expected a <category> tag: got {0} instead".format(category.tag))
            else:
                categories.append(CombinedOpenEndedRubric.extract_category(category))
        return categories

    @staticmethod
    def extract_category(category):
        '''
        construct an individual category
        {category: "Category 1 Name",
         options: [{text: "Option 1 text", points: 1},
                   {text: "Option 2 text", points: 2}]}

        all sorting and auto-point generation occurs in this function
        '''

        has_score=False
        descriptionxml = category[0]
        scorexml = category[1]
        if scorexml.tag == "option":
            optionsxml = category[1:]
        else:
            optionsxml = category[2:]
            has_score=True

        # parse description
        if descriptionxml.tag != 'description':
            raise Exception("[extract_category]: expected description tag, got {0} instead".format(descriptionxml.tag))

        if has_score:
            if scorexml.tag != 'score':
                raise Exception("[extract_category]: expected score tag, got {0} instead".format(scorexml.tag))

        for option in optionsxml:
            if option.tag != "option":
                raise Exception("[extract_category]: expected option tag, got {0} instead".format(option.tag))

        description = descriptionxml.text

        if has_score:
            score = int(scorexml.text)
        else:
            score = 0

        cur_points = 0
        options = []
        autonumbering = True
        # parse options
        for option in optionsxml:
            if option.tag != 'option':
                raise Exception("[extract_category]: expected option tag, got {0} instead".format(option.tag))
            else:
                pointstr = option.get("points")
                if pointstr:
                    autonumbering = False
                    # try to parse this into an int
                    try:
                        points = int(pointstr)
                    except ValueError:
                        raise Exception("[extract_category]: expected points to have int, got {0} instead".format(pointstr))
                elif autonumbering:
                    # use the generated one if we're in the right mode
                    points = cur_points
                    cur_points = cur_points + 1
                else:
                    raise Exception("[extract_category]: missing points attribute. Cannot continue to auto-create points values after a points value is explicitly dfined.")
                optiontext = option.text
                selected = False
                if has_score:
                    if points == score:
                        selected = True
                options.append({'text': option.text, 'points': points, 'selected' : selected})

        # sort and check for duplicates
        options = sorted(options, key=lambda option: option['points'])
        CombinedOpenEndedRubric.validate_options(options)

        return {'description': description, 'options': options, 'score' : score, 'has_score' : has_score}

    @staticmethod
    def validate_options(options):
        '''
        Validates a set of options. This can and should be extended to filter out other bad edge cases
        '''
        if len(options) == 0:
            raise Exception("[extract_category]: no options associated with this category")
        if len(options) == 1:
            return
        prev = options[0]['points']
        for option in options[1:]:
            if prev == option['points']:
                raise Exception("[extract_category]: found duplicate point values between two different options")
            else:
                prev = option['points']