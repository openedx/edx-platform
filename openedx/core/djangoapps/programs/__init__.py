"""
Platform support for Programs.

This package is a thin wrapper around interactions with the Programs service,
supporting learner- and author-facing features involving that service
if and only if the service is deployed in the Open edX installation.

To ensure maximum separation of concerns, and a minimum of interdependencies,
this package should be kept small, thin, and stateless.
"""

# Register signal handlers
from . import signals
