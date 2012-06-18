### 
### One-off script for importing courseware form XML format
###


#import mitxmako.middleware
#from courseware import content_parser
#from django.contrib.auth.models import User
import os.path
from StringIO import StringIO
from mako.template import Template
from mako.lookup import TemplateLookup

from django.core.management.base import BaseCommand
from keystore.django import keystore

from lxml import etree

class Command(BaseCommand):
    help = \
''' Run FTP server.'''
    def handle(self, *args, **options):
        print args
        data_dir = args[0]
 
        parser = etree.XMLParser(remove_comments = True)

        lookup = TemplateLookup(directories=[data_dir])
        template = lookup.get_template("course.xml")
        course_string = template.render(groups=[])
        course = etree.parse(StringIO(course_string), parser=parser)

        elements = list(course.iter())

        tag_to_category = {
            # Custom tags
            'videodev': 'Custom',
            'slides': 'Custom',
            'book': 'Custom',
            'image': 'Custom',
            'discuss': 'Custom',
            # Simple lists
            'chapter': 'Week',
            'course': 'Course',
            'sequential': 'LectureSequence',
            'vertical': 'ProblemSet',
            'section': {
                'Lab': 'Lab',
                'Lecture Sequence': 'LectureSequence',
                'Homework': 'Homework',
                'Tutorial Index': 'TutorialIndex',
                'Video': 'VideoSegment',
                'Midterm': 'Exam',
                'Final': 'Exam',
                None: 'Section',
            },
            # True types
            'video': 'VideoSegment',
            'html': 'HTML',
            'problem': 'Problem',
            }

        name_index = 0
        for e in elements:
            name = e.attrib.get('name', None)
            for f in elements:
                if f != e and f.attrib.get('name', None) == name:
                    name = None
            if not name:
                name = "{tag}_{index}".format(tag=e.tag, index=name_index)
                name_index = name_index + 1
            if e.tag in tag_to_category:
                category = tag_to_category[e.tag]
                if isinstance(category, dict):
                    category = category[e.get('format')]
                category = category.replace('/', '-')
                name = name.replace('/', '-')
                e.set('url', 'i4x://mit.edu/6002xs12/{category}/{name}'.format(
                    category=category,
                    name=name))


        def handle_skip(e):
            print "Skipping ", e

        results = {}

        def handle_custom(e):
            data = {'type':'i4x://mit.edu/6002xs12/tag/{tag}'.format(tag=e.tag),
                    'attrib':dict(e.attrib)}
            results[e.attrib['url']] = {'data':data}

        def handle_list(e):
            if e.attrib.get("class", None) == "tutorials":
                return
            children = [le.attrib['url'] for le in e.getchildren()]
            results[e.attrib['url']] = {'children':children}

        def handle_video(e):
            url = e.attrib['url']
            clip_url = url.replace('VideoSegment', 'VideoClip')
            # Take: 0.75:izygArpw-Qo,1.0:p2Q6BrNhdh8,1.25:1EeWXzPdhSA,1.50:rABDYkeK0x8
            # Make: [(0.75, 'izygArpw-Qo'), (1.0, 'p2Q6BrNhdh8'), (1.25, '1EeWXzPdhSA'), (1.5, 'rABDYkeK0x8')]
            youtube_str = e.attrib['youtube'] 
            youtube_list =  [(float(x), y) for x,y in map(lambda x:x.split(':'), youtube_str.split(','))]
            clip_infos = [{ "status": "ready", 
                            "format": "youtube", 
                            "sane": True, 
                            "location": "youtube", 
                            "speed": speed, 
                            "id": youtube_id, 
                            "size": None} \
                          for (speed, youtube_id) \
                              in youtube_list]
            results[clip_url] = {'data':{'clip_infos':clip_infos}}
            results[url] = {'children' : [{'url':clip_url}]}

        def handle_html(e):
            if 'src' in e.attrib:
                text = open(data_dir+'html/'+e.attrib['src']).read()
            else:
                textlist=[e.text]+[etree.tostring(elem) for elem in e]+[e.tail]
                textlist=[i for i in textlist if type(i)==str]
                text = "".join(textlist)

            results[e.attrib['url']] = {'data':{'text':text}}

        def handle_problem(e):
            data = open(os.path.join(data_dir, 'problems', e.attrib['filename']+'.xml')).read()
            results[e.attrib['url']] = {'data':{'statement':data}}

        element_actions = {# Inside HTML ==> Skip these
            'a': handle_skip,
            'h1': handle_skip,
            'h2': handle_skip,
            'hr': handle_skip,
            'strong': handle_skip,
            'ul': handle_skip,
            'li': handle_skip,
            'p': handle_skip,
            # Custom tags
            'videodev': handle_custom,
            'slides': handle_custom,
            'book': handle_custom,
            'image': handle_custom,
            'discuss': handle_custom,
            # Simple lists
            'chapter': handle_list,
            'course': handle_list,
            'sequential': handle_list,
            'vertical': handle_list,
            'section': handle_list,
            # True types
            'video': handle_video,
            'html': handle_html,
            'problem': handle_problem,
            }

        for e in elements:
            element_actions[e.tag](e)

        for k in results:
            keystore().create_item(k, 'Piotr Mitros')
            if 'data' in results[k]:
                keystore().update_item(k, results[k]['data'])
            if 'children' in results[k]:
                keystore().update_children(k, results[k]['children'])
