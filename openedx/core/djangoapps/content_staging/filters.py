"""
Filters that affect the behavior of staged content (and the clipboard)
"""
# pylint: disable=unused-argument
from __future__ import annotations

from attrs import asdict

from openedx_filters import PipelineStep
from openedx_filters.tooling import OpenEdxPublicFilter
from .data import StagedContentFileData
from .models import StagedContent


class StagingStaticAssetFilter(OpenEdxPublicFilter):
    """
    A filter used to determine which static assets associate with an XBlock(s)
    should be staged in the StagedContent app (e.g. the clipboard).

    This API is considered BETA. Once it is stable, this definition should be moved into openedx_filters.
    """

    filter_type = "org.openedx.content_authoring.staged_content.static_filter_source.v1"

    @classmethod
    def run_filter(cls, staged_content: StagedContent, file_datas: list[StagedContentFileData]):
        """
        Run this filter, which requires the following arguments:
            staged_content (StagedContent): details of the content being staged, as saved to the DB.
            file_datas (list[StagedContentFileData]): details of the files being staged
        """
        data = super().run_pipeline(staged_content=staged_content, file_datas=file_datas)
        return data.get("file_datas")


class IgnoreLargeFiles(PipelineStep):
    """
    Don't copy files over 10MB into the clipboard
    """

    # pylint: disable=arguments-differ
    def run_filter(self, staged_content: StagedContent, file_datas: list[StagedContentFileData]):
        """
        Filter the list of file_datas to remove any large files
        """
        limit = 10 * 1024 * 1024

        def remove_large_data(fd: StagedContentFileData):
            """ Remove 'data' from the immutable StagedContentFileData object, if it's above the size limit """
            if fd.data and len(fd.data) > limit:
                # these data objects are immutable so make a copy with data=None:
                return StagedContentFileData(**{**asdict(fd), "data": None})
            return fd

        return {"file_datas": [remove_large_data(fd) for fd in file_datas]}
