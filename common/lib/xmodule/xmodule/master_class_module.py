# -*- coding: utf-8 -*-
"""Word cloud is ungraded xblock used by students to
generate and view word cloud.

On the client side we show:
If student does not yet answered - `num_inputs` numbers of text inputs.
If student have answered - words he entered and cloud.
"""

import json
import logging

from pkg_resources import resource_string
from xmodule.raw_module import EmptyDataRawDescriptor
from xmodule.editing_module import MetadataOnlyEditingDescriptor
from xmodule.x_module import XModule
from django.contrib.auth.models import User

from xblock.fields import Scope, Dict, Boolean, List, Integer, String


log = logging.getLogger(__name__)

from django.utils.translation import ugettext as _


def pretty_bool(value):
    """Check value for possible `True` value.

    Using this function we can manage different type of Boolean value
    in xml files.
    """
    bool_dict = [True, "True", "true", "T", "t", "1"]
    return value in bool_dict


class MasterClassFields(object):
    """XFields for word cloud."""
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        scope=Scope.settings,
        default=_("Master Class")
    )
    total_places = Integer(
        display_name=_("Max places"),
        help=_("Number of places available for students to register for masterclass."),
        scope=Scope.settings,
        default=30,
        values={"min": 1}
    )
    autopass_score = Integer(
        display_name=_("Autopass score"),
        help=_("Autopass score to automaticly pass registration for masterclass."),
        scope=Scope.settings,
        default=250,
        values={"min": 1}
    )

    # Fields for descriptor.
    submitted = Boolean(
        help=_("Whether this student has been register for this master class."),
        scope=Scope.user_state,
        default=False
    )
    all_registrations = List(
        help=_("All registrations from all students."),
        scope=Scope.user_state_summary
    )
    passed_registrations = List(
        help=_("Passed registrations."),
        scope=Scope.user_state_summary
    )


class MasterClassModule(MasterClassFields, XModule):
    """MasterClass Xmodule"""
    js = {
        'coffee': [resource_string(__name__, 'js/src/javascript_loader.coffee')],
        'js': [resource_string(__name__, 'js/src/word_cloud/d3.min.js'),
        resource_string(__name__, 'js/src/word_cloud/d3.layout.cloud.js'),
        resource_string(__name__, 'js/src/master_class/master_class.js'),
        resource_string(__name__, 'js/src/master_class/master_class_main.js')]
    }
    css = {'scss': [resource_string(__name__, 'css/master_class/display.scss')]}
    js_module_name = "MasterClass"

    def get_state(self):
        """Return success json answer for client."""
        total_register = len(self.passed_registrations)
        message = ""
        if self.runtime.user.email in self.passed_registrations:
            message = _("You have been registered for this master class. We will provide addition information soon.")
        else:
            message = _("You are pending for registration for this master class. Please visit this page later for result.")
        if (total_register is None):
            total_register = 0
        additional_data = {}
        if self.runtime.user_is_staff:
            additional_data['all_registrations'] = self.all_registrations
            additional_data['passed_registrations'] = self.passed_registrations
            additional_data['is_staff'] = self.runtime.user_is_staff
        if self.submitted:
            data = {
                'status': 'success',
                'submitted': True,
                'total_places': self.total_places,
                'total_register': total_register,
                'message': message
            }
            data.update(additional_data)
            return json.dumps(data)
        else:
            data = {
                'status': 'success',
                'submitted': False,
                'total_places': self.total_places,
                'total_register': total_register,
            }
            data.update(additional_data)
            return json.dumps(data)

    def handle_ajax(self, dispatch, data):
        """Ajax handler.

        Args:
            dispatch: string request slug
            data: dict request get parameters

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
            master_class = data.getall('master_class[]')

            self.all_registrations.append(self.runtime.user.email)

            self.submitted = True

            return self.get_state()
        elif dispatch == 'get_state':
            return self.get_state()
        elif dispatch == 'register':
            logging.error(data)
            if self.runtime.user_is_staff:
                for email in data.getall('emails[]'):
                    if (len(self.passed_registrations) < self.total_places):
                        if (self.all_registrations.count(email) > 0):
                            self.passed_registrations.append(email)
                            self.all_registrations.remove(email)
                    else:
                        break
                return self.get_state()
            else:
                return json.dumps({
                    'status': 'fail',
                    'error': 'Unknown Command!'
                })
        elif dispatch == 'csv':
            if self.runtime.user_is_staff:
                header = [u'Email', u'ФИО']
                datatable = {'header': header, 'students': []}
                data = []
                for email in self.passed_registrations:
                    datarow = []
                    user = User.objects.get(email=email)
                    datarow += [user.email, user.profile.name]
                    data += [datarow]
                datatable['data'] = data

                return json.dumps({'status': 'success', 'data': datatable})
            else:
                return json.dumps({
                    'status': 'fail',
                    'error': 'Unknown Command!'
                })

        else:
            return json.dumps({
                'status': 'fail',
                'error': 'Unknown Command!'
            })

    def get_html(self):
        """Template rendering."""
        logging.info(type(self.location))
        logging.info(self.get_progress())
        logging.info(self.runtime.seed)
        logging.info(self.runtime.anonymous_student_id)
        logging.info(self.runtime)
        context = {
            'display_name': self.display_name,
            'element_id': self.location.html_id(),
            'element_class': self.location.category,
            'ajax_url': self.system.ajax_url,
            'submitted': self.submitted,
            'is_staff': self.runtime.user_is_staff,
            'all_registrations': self.all_registrations,
            'passed_registrations': self.passed_registrations
        }
        self.content = self.system.render_template('master_class.html', context)
        return self.content


class MasterClassDescriptor(MasterClassFields, MetadataOnlyEditingDescriptor, EmptyDataRawDescriptor):
    """Descriptor for MasterClass Xmodule."""
    module_class = MasterClassModule
    template_dir_name = 'master_class'
