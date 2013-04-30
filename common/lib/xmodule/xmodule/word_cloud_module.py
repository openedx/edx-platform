"""Word cloud is ungraded xblock used by students to
generate and view word cloud.

On the client side we show:
If student does not yet anwered - `num_inputs` numbers of text inputs.
If student have answered - words he entered and cloud.
"""

import json
import logging

from pkg_resources import resource_string
from xmodule.raw_module import RawDescriptor
from xmodule.x_module import XModule

from xblock.core import Scope, String, Object, Boolean, List, Integer

log = logging.getLogger(__name__)


def pretty_bool(value):
    BOOL_DICT = [True, "True", "true", "T", "t", "1"]
    return value in BOOL_DICT


class WordCloudDescriptorFields(object):
    """Word Cloud fields from xml for descriptor."""
    display_name = String(
        help="Display name for this module",
        scope=Scope.settings
    )
    num_inputs = Integer(
        help="Number of inputs.",
        scope=Scope.settings,
        default=5
    )
    num_top_words = Integer(
        help="Number of max words, which will be displayed.",
        scope=Scope.settings,
        default=250
    )
    display_student_percents = Boolean(
        help="Dispaly usage percents for each word.",
        scope=Scope.settings,
        default=True
    )


class WordCloudFields(object):
    submitted = Boolean(
        help="Whether this student has posted words to the cloud.",
        scope=Scope.user_state,
        default=False
    )
    student_words = List(
        help="Student answer.",
        scope=Scope.user_state,
        default=[]
    )
    all_words = Object(
        help="All possible words from other students.",
        scope=Scope.content
    )
    top_words = Object(
        help="Top N words for word cloud.",
        scope=Scope.content
    )


class WordCloudModule(WordCloudFields, WordCloudDescriptorFields, XModule):
    """WordCloud Xmodule"""
    js = {
        'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee')],
        'js': [resource_string(__name__, 'js/src/word_cloud/logme.js'),
        resource_string(__name__, 'js/src/word_cloud/d3.min.js'),
        resource_string(__name__, 'js/src/word_cloud/d3.layout.cloud.js'),
        resource_string(__name__, 'js/src/word_cloud/word_cloud.js'),
        resource_string(__name__, 'js/src/word_cloud/word_cloud_main.js')]
    }
    css = {'scss': [resource_string(__name__, 'css/word_cloud/display.scss')]}
    js_module_name = "WordCloud"

    def get_state(self):
        """Return success json answer for client."""
        if self.submitted:
            total_count = sum(self.all_words.itervalues())
            return json.dumps({
                'status': 'success',
                'submitted': True,
                'display_student_percents': pretty_bool(
                    self.display_student_percents
                ),
                'student_words': {
                    word: self.all_words[word] for word in self.student_words
                },
                'total_count': total_count,
                'top_words': self.prepare_words(self.top_words, total_count)
            })
        else:
            return json.dumps({
                'status': 'success',
                'submitted': False,
                'display_student_percents': False,
                'student_words': {},
                'total_count': 0,
                'top_words': {}
            })

    def good_word(self, word):
        """Convert raw word to suitable word."""
        return word.strip().lower()

    def prepare_words(self, top_words, total_count):
        """Convert words dictionary for client API."""
        list_to_return = []
        percents = 0
        for num, word_tuple in enumerate(top_words.iteritems()):
            if num == len(top_words) - 1:
                percent = 100 - percents
            else:
                percent = round(100.0 * word_tuple[1] / total_count)
                percents += percent
            list_to_return.append(
                {
                    'text': word_tuple[0],
                    'size': word_tuple[1],
                    'percent': percent
                }
            )
        return list_to_return

    def top_dict(self, dict_obj, amount):
        """Return new dict: top of dict using dict value."""
        return dict(
            sorted(
                dict_obj.items(),
                key=lambda x: x[1],
                reverse=True
            )[:amount]
        )

    def handle_ajax(self, dispatch, post):
        """Ajax handler.

        Args:
            dispatch: string request slug
            post: dict request get parameters

        Returns:
            json string
        """
        if dispatch == 'submit':
            if self.submitted:
                return json.dumps({
                    'status': 'fail',
                    'error': 'You have already posted your data.'
                })

            # Student words from client.
            # FIXME: we must use raw JSON, not a post data (multipart/form-data)
            raw_student_words = post.getlist('student_words[]')
            student_words = filter(None, map(self.good_word, raw_student_words))

            self.student_words = student_words

            # FIXME: fix this, when xblock will support mutable types.
            # Now we use this hack.
            # speed issues
            temp_all_words = self.all_words

            self.submitted = True

            # Save in all_words.
            for word in self.student_words:
                temp_all_words[word] = temp_all_words.get(word, 0) + 1

            # Update top_words.
            self.top_words = self.top_dict(
                temp_all_words,
                int(self.num_top_words)
            )

            # Save all_words in database.
            self.all_words = temp_all_words

            return self.get_state()
        elif dispatch == 'get_state':
            return self.get_state()
        else:
            return json.dumps({
                'status': 'fail',
                'error': 'Unknown Command!'
            })

    def get_html(self):
        """Template rendering."""
        context = {
            'element_id': self.location.html_id(),
            'element_class': self.location.category,
            'ajax_url': self.system.ajax_url,
            'num_inputs': int(self.num_inputs),
            'submitted': self.submitted
        }
        self.content = self.system.render_template('word_cloud.html', context)
        return self.content


class WordCloudDescriptor(WordCloudDescriptorFields, RawDescriptor):
    """Descriptor for WordCloud Xmodule."""
    module_class = WordCloudModule
    template_dir_name = 'word_cloud'
    stores_state = True
    mako_template = "widgets/raw-edit.html"
