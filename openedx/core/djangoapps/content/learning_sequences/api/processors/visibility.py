"""
Simple OutlineProcessor that removes items based on VisibilityData.
"""

from .base import OutlineProcessor


class VisibilityOutlineProcessor(OutlineProcessor):
    """
    Simple OutlineProcessor that removes items based on VisibilityData.

    We only remove items with this Processor, we never make them visible-but-
    inaccessible. There is no need to implement `load_data` because everything
    we need comes from the CourseOutlineData itself.
    """
    def usage_keys_to_remove(self, full_course_outline):
        """
        Remove anything flagged with `hide_from_toc` or `visible_to_staff_only`.

        It's possible to argue that we should include `hide_from_toc` items in
        the outline, but flag them in a special way. Students aren't precisely
        forbidden from knowing that these items exist, they just aren't supposed
        to see them in the course navigation. That being said, a) this is an
        obscure and long-deprecated feature; b) this implementation will
        preserve the behavior that students won't see it (though staff will);
        and c) it simplifies REST API clients to never have to deal with the
        concept at all.
        """
        def should_remove(visibility):
            return visibility.hide_from_toc or visibility.visible_to_staff_only

        sections_to_remove = {
            sec.usage_key
            for sec in full_course_outline.sections
            if should_remove(sec.visibility)
        }
        seqs_to_remove = {
            seq.usage_key
            for seq in full_course_outline.sequences.values()
            if should_remove(seq.visibility)
        }
        return frozenset(sections_to_remove | seqs_to_remove)
