# -*- coding: utf-8 -*-
"""Word cloud is ungraded xblock used by students to
generate and view word cloud.

On the client side we show:
If student does not yet answered - `num_inputs` numbers of text inputs.
If student have answered - words he entered and cloud.
"""

import json
import logging
import datetime
import csv
import StringIO

from pkg_resources import resource_string
from xmodule.raw_module import EmptyDataRawDescriptor
from xmodule.editing_module import MetadataOnlyEditingDescriptor
from xmodule.x_module import XModule
from django.contrib.auth.models import User

from django.utils.timezone import UTC

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
        allreg = []
        passreg = []

        for email in self.all_registrations:
            user = User.objects.get(email=email)
            allreg += [{'email': email, 'name': user.profile.lastname + ' ' + user.profile.firstname + ' ' + user.profile.middlename}]
        for email in self.passed_registrations:
            user = User.objects.get(email=email)
            passreg += [{'email': email, 'name': user.profile.lastname + ' ' + user.profile.firstname + ' ' + user.profile.middlename}]

        if self.runtime.user_is_staff:
            additional_data['all_registrations'] = allreg
            additional_data['passed_registrations'] = passreg
            additional_data['is_staff'] = self.runtime.user_is_staff
            additional_data['csv_name'] = self.runtime.course_id + " " + self.display_name

        if self.submitted and self.runtime.user.email not in self.all_registrations and self.runtime.user.email not in self.passed_registrations:
            self.submitted = False
        if self.submitted:
            data = {
                'status': 'success',
                'submitted': True,
                'is_closed': self.is_past_due(),
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
                'is_closed': self.is_past_due(),
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
            if self.is_past_due():
                return json.dumps({
                    'status': 'fail',
                    'error': 'Registration is closed due to date.'
                })
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
        elif dispatch == 'unregister':
            logging.error(data)
            if self.runtime.user_is_staff:
                for email in data.getall('emails[]'):
                    if (self.passed_registrations.count(email) > 0):
                        self.passed_registrations.remove(email)
                        self.all_registrations.append(email)
                return self.get_state()
            else:
                return json.dumps({
                    'status': 'fail',
                    'error': 'Unknown Command!'
                })
        elif dispatch == 'remove':
            logging.error(data)
            if self.runtime.user_is_staff:
                for email in data.getall('emails[]'):
                    if (self.passed_registrations.count(email) > 0):
                        self.passed_registrations.remove(email)
                    if (self.all_registrations.count(email) > 0):
                        self.all_registrations.remove(email)
                return self.get_state()
            else:
                return json.dumps({
                    'status': 'fail',
                    'error': 'Unknown Command!'
                })
        elif dispatch == 'csv':
            if self.runtime.user_is_staff:
                header = [u'Email', u'Фамилия', u'Имя', u'Отчество',]
                datatable = {'header': header, 'students': []}
                data = []
                for email in self.passed_registrations:
                    datarow = []
                    user = User.objects.get(email=email)
                    datarow += [user.email, user.profile.lastname, user.profile.firstname, user.profile.middlename]
                    data += [datarow]
                datatable['data'] = data

                return self.return_csv("   ", datatable, encoding="cp1251", dialect="excel-tab")
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

    def is_past_due(self):
        """
        Is it now past this problem's due date, including grace period?
        """
        return (self.due is not None and
                datetime.datetime.now(UTC()) > self.due)

    def get_html(self):
        """Template rendering."""
        logging.info(type(self.location))
        logging.info(self.get_progress())
        logging.info(self.runtime.seed)
        logging.info(self.runtime.anonymous_student_id)
        logging.info(self.runtime)
        context = {
            'display_name': self.display_name,
            'due': self.due,
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
    def return_csv(self, func, datatable, file_pointer=None, encoding="utf-8", dialect="excel"):
        """Outputs a CSV file from the contents of a datatable."""
        if file_pointer is None:
            response = StringIO.StringIO()
        else:
            response = file_pointer
        writer = csv.writer(response, dialect=dialect, quotechar='"', quoting=csv.QUOTE_ALL)
        encoded_row = [unicode(s).encode(encoding) for s in datatable['header']]
        writer.writerow(encoded_row)
        for datarow in datatable['data']:
            encoded_row = [unicode(s).encode(encoding) for s in datarow]
            writer.writerow(encoded_row)
        if file_pointer is None:
            return response.getvalue()
        else:
            return response


class MasterClassDescriptor(MasterClassFields, MetadataOnlyEditingDescriptor, EmptyDataRawDescriptor):
    """Descriptor for MasterClass Xmodule."""
    module_class = MasterClassModule
    template_dir_name = 'master_class'
