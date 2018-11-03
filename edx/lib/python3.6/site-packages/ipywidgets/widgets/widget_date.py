# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""Color class.

Represents an HTML Color .
"""

from .widget_description import DescriptionWidget
from .valuewidget import ValueWidget
from .widget import register
from .widget_core import CoreWidget
from .trait_types import Date, date_serialization
from traitlets import Unicode, Bool


@register
class DatePicker(DescriptionWidget, ValueWidget, CoreWidget):
    value = Date(None, allow_none=True).tag(sync=True, **date_serialization)
    disabled = Bool(False, help="Enable or disable user changes.").tag(sync=True)


    _view_name = Unicode('DatePickerView').tag(sync=True)
    _model_name = Unicode('DatePickerModel').tag(sync=True)
