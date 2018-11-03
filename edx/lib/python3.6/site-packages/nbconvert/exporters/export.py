"""Deprecated as of 5.0 use nbconvert.exporters.base."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import warnings 
warnings.warn("""`nbconvert.exporters.export` has been deprecated in favor of `nbconvert.exporters.base` since nbconvert 5.0.""",
    DeprecationWarning)

from .exporter_locator import *
