"""Outline Roots API.

This module provides functions to manage outline roots.
"""
from dataclasses import dataclass
from datetime import datetime

from django.db.transaction import atomic

from openedx_learning.api.authoring_models import (
    Container,
    ContainerVersion,
    Section,
    SectionVersion,
    Subsection,
    SubsectionVersion,
    Unit,
    UnitVersion,
)
from openedx_learning.api import authoring as authoring_api

from .models import OutlineRoot, OutlineRootVersion

# 🛑 UNSTABLE: All APIs related to containers are unstable until we've figured
#              out our approach to dynamic content (randomized, A/B tests, etc.)
__all__ = [
    "create_outline_root",
    "create_outline_root_version",
    "create_next_outline_root_version",
    "create_outline_root_and_version",
    "get_outline_root",
    "get_outline_root_version",
    "OutlineRootListEntry",
    "get_children_in_outline_root",
]


def create_outline_root(
    learning_package_id: int,
    key: str,
    *,
    created: datetime,
    created_by: int | None,
) -> OutlineRoot:
    """
    [ 🛑 UNSTABLE ] Create a new OutlineRoot.

    Args:
        learning_package_id: The learning package ID.
        key: The key.
        created: The creation date.
        created_by: The user who created the OutlineRoot.
    """
    return authoring_api.create_container(
        learning_package_id,
        key,
        created,
        created_by,
        can_stand_alone=True,  # Not created as part of another container.
        container_cls=OutlineRoot,
    )


def create_outline_root_version(
    outline_root: OutlineRoot,
    version_num: int,
    *,
    title: str,
    entity_rows: list[authoring_api.ContainerEntityRow],
    created: datetime,
    created_by: int | None = None,
) -> OutlineRootVersion:
    """
    [ 🛑 UNSTABLE ] Create a new OutlineRoot version.

    This is a very low-level API, likely only needed for import/export. In
    general, you will use `create_outline_root_and_version()` and
    `create_next_outline_root_version()` instead.

    Args:
        outline_root: The OutlineRoot
        version_num: The version number.
        title: The title.
        entity_rows: child entities/versions
        created: The creation date.
        created_by: The user who created this version of the outline root.
    """
    return authoring_api.create_container_version(
        outline_root.pk,
        version_num,
        title=title,
        entity_rows=entity_rows,
        created=created,
        created_by=created_by,
        container_version_cls=OutlineRootVersion,
    )


def _make_entity_rows(
    children: list[Section | SectionVersion | Subsection | SubsectionVersion | Unit | UnitVersion] | None,
) -> list[authoring_api.ContainerEntityRow] | None:
    """
    Helper method: given a list of children for the outline root, return the
    lists of ContainerEntityRows (entity+version pairs) needed for the
    base container APIs.

    *Version objects are passed when we want to pin a specific version, otherwise
    Section/Subsection/Unit is used for unpinned.
    """
    if children is None:
        # When these are None, that means don't change the entities in the list.
        return None
    return [
        (
            authoring_api.ContainerEntityRow(
                entity_pk=s.container.publishable_entity_id,
                version_pk=None,
            ) if isinstance(s, (Section, Subsection, Unit))
            else authoring_api.ContainerEntityRow(
                entity_pk=s.container_version.container.publishable_entity_id,
                version_pk=s.container_version.publishable_entity_version_id,
            )
        )
        for s in children
    ]


def create_next_outline_root_version(
    outline_root: OutlineRoot,
    *,
    title: str | None = None,
    children: list[Section | SectionVersion | Subsection | SubsectionVersion | Unit | UnitVersion] | None = None,
    created: datetime,
    created_by: int | None = None,
    entities_action: authoring_api.ChildrenEntitiesAction = authoring_api.ChildrenEntitiesAction.REPLACE,
) -> OutlineRootVersion:
    """
    [ 🛑 UNSTABLE ] Create the next OutlineRoot version.

    Args:
        outline_root: The OutlineRoot
        title: The title. Leave as None to keep the current title.
        children: The children, usually a list of Sections. Pass SectionVersions to pin to specific versions.
            Passing None will leave the existing children unchanged.
        created: The creation date.
        created_by: The user who created the section.
    """
    entity_rows = _make_entity_rows(children)
    return authoring_api.create_next_container_version(
        outline_root.pk,
        title=title,
        entity_rows=entity_rows,
        created=created,
        created_by=created_by,
        container_version_cls=OutlineRootVersion,
        entities_action=entities_action,
    )


def create_outline_root_and_version(
    learning_package_id: int,
    key: str,
    *,
    title: str,
    children: list[Section | SectionVersion | Subsection | SubsectionVersion | Unit | UnitVersion] | None = None,
    created: datetime,
    created_by: int | None = None,
) -> tuple[OutlineRoot, OutlineRootVersion]:
    """
    [ 🛑 UNSTABLE ] Create a new OutlineRoot and its version.

    Args:
        learning_package_id: The learning package ID.
        key: The key. We don't really want a "key" for our OutlineRoots, but
            we're required to set something here, so by convention this should
            be the course ID in the form 'course-root-v1:org+course_id+run'.
        created: The creation date.
        created_by: The user who created the section.
        can_stand_alone: Set to False when created as part of containers
    """
    entity_rows = _make_entity_rows(children)
    with atomic():
        outline_root = create_outline_root(
            learning_package_id,
            key,
            created=created,
            created_by=created_by,
        )
        version = create_outline_root_version(
            outline_root,
            1,
            title=title,
            entity_rows=entity_rows or [],
            created=created,
            created_by=created_by,
        )
    return outline_root, version


def get_outline_root(outline_root_pk: int) -> OutlineRoot:
    """
    [ 🛑 UNSTABLE ] Get an OutlineRoot.

    Args:
        outline_root_pk: The OutlineRoot ID.
    """
    return OutlineRoot.objects.get(pk=outline_root_pk)


def get_outline_root_version(outline_root_version_pk: int) -> OutlineRootVersion:
    """
    [ 🛑 UNSTABLE ] Get a OutlineRootVersion.

    Args:
        outline_root_version_pk: The OutlineRootVersion ID.
    """
    return OutlineRootVersion.objects.get(pk=outline_root_version_pk)


@dataclass(frozen=True)
class OutlineRootListEntry:
    """
    [ 🛑 UNSTABLE ]
    Data about a single entity in a container, e.g. a section in an outline root.
    """
    child_version: SectionVersion | SubsectionVersion | UnitVersion
    pinned: bool = False

    @property
    def container(self) -> Container:
        return self.container_version.container

    @property
    def container_version(self) -> ContainerVersion:
        return self.child_version.container_version


def get_children_in_outline_root(
    outline_root: OutlineRoot,
    *,
    published: bool,
) -> list[OutlineRootListEntry]:
    """
    [ 🛑 UNSTABLE ]
    Get the list of entities and their versions in the draft or published
    version of the given OutlineRoot.

    Args:
        outline_root: The OutlineRoot, e.g. returned by `get_outline_root()`
        published: `True` if we want the published version of the OutlineRoot,
            or `False` for the draft version.
    """
    assert isinstance(outline_root, OutlineRoot)
    children = []
    for entry in authoring_api.get_entities_in_container(outline_root, published=published):
        # Convert from generic ContainerEntityListEntry to OutlineRootListEntry for convenience and better type safety:
        child_container_version = entry.entity_version.containerversion
        if hasattr(child_container_version, "section"):
            child_version = child_container_version.section
        elif hasattr(child_container_version, "subsection"):
            child_version = child_container_version.subsection
        elif hasattr(child_container_version, "unit"):
            child_version = child_container_version.unit
        else:
            raise TypeError(f"OutlineRoot {outline_root.pk} had unexpected child {child_container_version}")
        children.append(OutlineRootListEntry(child_version=child_version, pinned=entry.pinned))
    return children
