"""
Content Library Transformer.
"""
from __future__ import annotations

import json
import logging
from functools import partial
from typing import Any, Callable


from eventtracking import tracker
from opaque_keys.edx.keys import UsageKey

from common.djangoapps.track import contexts
from lms.djangoapps.courseware.models import StudentModule
from openedx.core.djangoapps.content.block_structure.block_structure import (
    BlockStructureModulestoreData,
    BlockStructureBlockData,
)
from openedx.core.djangoapps.content.block_structure.transformer import (
    BlockStructureTransformer,
    FilteringTransformerMixin
)
from xmodule.library_content_block import LibraryContentBlock  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.util.keys import BlockKey

from ..utils import get_student_module_as_dict

logger = logging.getLogger(__name__)


class ContentLibraryTransformer(FilteringTransformerMixin, BlockStructureTransformer):
    """
    A transformer that manipulates the block structure by removing all
    blocks within a library_content block to which a user should not
    have access.

    Staff users are not to be exempted from library content pathways.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls) -> str:
        """
        Unique identifier for the transformer's class;
        same identifier used in setup.py.
        """
        return "library_content"

    @classmethod
    def collect(cls, block_structure: BlockStructureModulestoreData) -> None:
        """
        Collects any information that's necessary to execute this
        transformer's transform method.
        """
        block_structure.request_xblock_fields('mode')
        block_structure.request_xblock_fields('shuffle')
        block_structure.request_xblock_fields('max_count')
        block_structure.request_xblock_fields('manual')
        block_structure.request_xblock_fields('candidates')
        block_structure.request_xblock_fields('source_library_id')
        block_structure.request_xblock_fields('category')
        store = modulestore()

        # needed for analytics purposes
        def summarize_block(usage_key: UsageKey) -> dict[str, str | None]:
            """ Basic information about the given block """
            orig_key, orig_version = store.get_block_original_usage(usage_key)
            return {
                "usage_key": str(usage_key),
                "original_usage_key": str(orig_key) if orig_key else None,
                "original_usage_version": str(orig_version) if orig_version else None,
            }

        # For each block check if block is library_content.
        # If library_content add children array to content_library_children field
        for block_key in block_structure.topological_traversal(
                filter_func=lambda block_key: block_key.block_type == 'library_content',
                yield_descendants_of_unyielded=True,
        ):
            xblock = block_structure.get_xblock(block_key)
            for child_key in xblock.children:
                summary = summarize_block(child_key)
                block_structure.set_transformer_block_field(child_key, cls, 'block_analytics_summary', summary)

    def transform_block_filters(
        self,
        usage_info: Any,
        block_structure: BlockStructureBlockData,
    ) -> list[Callable[[UsageKey], bool]]:
        """
        Returns a list of functions which filter blocks out of this user's structure.

        For this particular Transformer, we only need one filter:
        "given a block, remove it IFF it's under a library_content block BUT it is not selected for this user"
        """
        all_library_children: set[UsageKey] = set()
        all_selected_children: set[UsageKey] = set()
        for block_key in block_structure:
            if block_key.block_type != 'library_content':
                continue
            library_children = block_structure.get_children(block_key)
            if library_children:
                all_library_children.update(library_children)
                selected: list[BlockKey] = []
                shuffle: bool = block_structure.get_xblock_field(block_key, 'shuffle')
                manual: bool = block_structure.get_xblock_field(block_key, 'manual')
                max_count: int = block_structure.get_xblock_field(block_key, 'max_count')
                candidates: list[UsageKey] = [
                    UsageKey.from_string(key_string)
                    for key_string in block_structure.get_xblock_field(block_key, 'candidates')
                ]
                source_library_id: str = block_structure.get_xblock_field(block_key, 'source_library_id')

                if max_count < 0:
                    max_count = len(library_children)

                # Retrieve "selected" json from LMS MySQL database.
                state_dict = get_student_module_as_dict(usage_info.user, usage_info.course_key, block_key)
                for selected_block in state_dict.get('selected', []):
                    # Add all selected entries for this user for this
                    # library block to the selected list.
                    block_type, block_id = selected_block
                    usage_key = usage_info.course_key.make_usage_key(*selected_block)
                    if usage_key in library_children:
                        selected.append(BlockKey(*selected_block))

                # Update selected
                previous_count = len(selected)
                block_keys = LibraryContentBlock.make_selection(
                    usage_key=block_key,
                    old_selected=selected,
                    all_children=library_children,
                    candidates=candidates,
                    max_count=max_count,
                    manual=manual,
                    shuffle=shuffle,
                )
                selected = block_keys['selected']

                # Save back any changes
                if any(block_keys[changed] for changed in ('invalid', 'overlimit', 'added')):
                    state_dict['selected'] = selected
                    StudentModule.save_state(
                        student=usage_info.user,
                        course_id=usage_info.course_key,
                        module_state_key=block_key,
                        defaults={
                            'state': json.dumps(state_dict),
                        },
                    )

                # publish events for analytics
                self._publish_events(
                    block_structure,
                    block_key,
                    previous_count,
                    max_count,
                    block_keys,
                    usage_info.user.id,
                )
                all_selected_children.update(usage_info.course_key.make_usage_key(*s) for s in selected)

        def check_child_removal(block_key: UsageKey):
            """
            Return True if selected block should be removed.

            Block is removed if it is part of library_content, but has
            not been selected for current user.
            """
            if block_key not in all_library_children:
                return False
            if block_key in all_selected_children:
                return False
            return True

        return [block_structure.create_removal_filter(check_child_removal)]

    def _publish_events(
        self,
        block_structure: BlockStructureBlockData,
        location: UsageKey,
        previous_count: int,
        max_count: int,
        block_keys: dict[str, list[BlockKey]],
        user_id,
    ) -> None:
        """
        Helper method to publish events for analytics purposes
        """

        def format_block_keys(keys: list[BlockKey]) -> list:
            """
            Helper function to format block keys
            """
            json_result = []
            for key in keys:
                info = block_structure.get_transformer_block_field(
                    key, ContentLibraryTransformer, 'block_analytics_summary'
                )
                json_result.append(info)
            return json_result

        def publish_event(event_name: str, result: list, **kwargs) -> None:
            """
            Helper function to publish an event for analytics purposes
            """
            event_data = {
                "location": str(location),
                "previous_count": previous_count,
                "result": result,
                "max_count": max_count,
            }
            event_data.update(kwargs)
            context = contexts.course_context_from_course_id(location.course_key)
            if user_id:
                context['user_id'] = user_id
            full_event_name = f"edx.librarycontentblock.content.{event_name}"
            with tracker.get_tracker().context(full_event_name, context):
                tracker.emit(full_event_name, event_data)

        LibraryContentBlock.publish_selected_children_events(
            block_keys,
            format_block_keys,
            publish_event,
        )


class ContentLibraryOrderTransformer(BlockStructureTransformer):
    """
    A transformer that manipulates the block structure by modifying the order of the
    selected blocks within a library_content block to match the order of the selections
    made by the ContentLibraryTransformer or the corresponding XBlock. So this transformer
    requires the selections for the randomized content block to be already
    made either by the ContentLibraryTransformer or the XBlock.

    Staff users are *not* exempted from library content pathways.
    """
    WRITE_VERSION = 1
    READ_VERSION = 1

    @classmethod
    def name(cls) -> str:
        """
        Unique identifier for the transformer's class;
        same identifier used in setup.py
        """
        return "library_content_randomize"

    @classmethod
    def collect(cls, block_structure: BlockStructureModulestoreData) -> None:
        """
        Collects any information that's necessary to execute this
        transformer's transform method.
        """
        # There is nothing to collect

    def transform(self, usage_info: Any, block_structure: BlockStructureBlockData) -> None:
        """
        Transforms the order of the children of the randomized content block
        to match the order of the selections made and stored in the XBlock 'selected' field.
        """
        for block_key in block_structure:
            if block_key.block_type != 'library_content':
                continue

            library_children: list[UsageKey] = block_structure.get_children(block_key)

            if library_children:
                state_dict = get_student_module_as_dict(usage_info.user, usage_info.course_key, block_key)
                current_children_blocks: set[str] = {
                    block.block_id for block in library_children
                }
                current_selected_blocks: set[str] = {
                    block_id for _block_type, block_id in state_dict.get('selected', [])
                }

                # As the selections should have already been made by the ContentLibraryTransformer,
                # the current children of the library_content block should be the same as the stored
                # selections. If they aren't, some other transformer that ran before this transformer
                # has modified those blocks (for example, content gating may have affected this). So do not
                # transform the order in that case.
                if current_children_blocks != current_selected_blocks:
                    logger.debug(
                        'Mismatch between the children of %s in the stored state and the actual children for user %s. '
                        'Continuing without order transformation.',
                        str(block_key),
                        usage_info.user.username
                    )
                else:
                    ordering_data: dict[str, int] = {
                        block_id: position
                        for position, (_block_type, block_id)
                        in enumerate(state_dict['selected'])
                    }
                    get_position_for_child: Callable[[UsageKey], int] = partial(
                        lambda child_usage_key, ordering: ordering[child_usage_key.block_id],
                        ordering_data,  # Avoid directly using ordering_data in lambda, since it's a loop variable.
                    )
                    library_children.sort(key=get_position_for_child)
