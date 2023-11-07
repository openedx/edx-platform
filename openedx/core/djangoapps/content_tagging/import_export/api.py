"""
Import API functions

This is overriden in edx-platform to add the `orgs` parameter to the `create_taxonomy_and_import_tags` function.
"""
from __future__ import annotations

from io import BytesIO

import openedx_tagging.core.tagging.import_export.api as oel_tagging_import_export_api
from openedx_tagging.core.tagging.import_export.parsers import ParserFormat
from organizations.models import Organization

from .. import api as taxonomy_api

def create_taxonomy_and_import_tags(
    taxonomy_name: str,
    taxonomy_description: str,
    file: BytesIO,
    parser_format: ParserFormat,
    orgs: list[Organization] | None = None,
) -> bool:
    """
    Create a taxonomy and import the tags from `file`, associating them with the provided `orgs`.
    """



