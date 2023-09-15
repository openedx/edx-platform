"""
Test for Content models
"""
import ddt
from django.test.testcases import TestCase

from openedx_tagging.core.tagging.models import (
    ObjectTag,
    Tag,
)
from openedx_tagging.core.tagging.api import create_taxonomy
from ..models import (
    ContentLanguageTaxonomy,
    ContentAuthorTaxonomy,
)


@ddt.ddt
class TestSystemDefinedModels(TestCase):
    """
    Test for System defined models
    """

    @ddt.data(
        (ContentLanguageTaxonomy, "taxonomy"),  # Invalid object key
        (ContentLanguageTaxonomy, "tag"),  # Invalid external_id, invalid language
        (ContentLanguageTaxonomy, "object"),  # Invalid object key
        (ContentAuthorTaxonomy, "taxonomy"),  # Invalid object key
        (ContentAuthorTaxonomy, "tag"),  # Invalid external_id, User don't exits
        (ContentAuthorTaxonomy, "object"),  # Invalid object key
    )
    @ddt.unpack
    def test_validations(
        self,
        taxonomy_cls,
        check,
    ):
        """
        Test that the respective validations are being called
        """
        taxonomy = create_taxonomy(
            name='Test taxonomy',
            taxonomy_class=taxonomy_cls,
        )

        tag = Tag(
            value="value",
            external_id="external_id",
            taxonomy=taxonomy,
        )
        tag.save()

        object_tag = ObjectTag(
            object_id='object_id',
            taxonomy=taxonomy,
            tag=tag,
        )

        check_taxonomy = check == 'taxonomy'
        check_object = check == 'object'
        check_tag = check == 'tag'
        assert not taxonomy.validate_object_tag(
            object_tag=object_tag,
            check_taxonomy=check_taxonomy,
            check_object=check_object,
            check_tag=check_tag,
        )
