Status: Deprecated (DEPR-24)

Responsibilities
================
XModules render specific course run content types to users for both authoring and learning. For instance, there is an XModule for Videos, another for HTML snippets, and another for Sequences. This package provides both the implementations of these XModules as well as some supporting utilities.

Direction: Convert and Extract
==============================
XModule exists today as a complex set of compatibility shims on top of XBlock (all XModules currently inherit from XBlock). The goal is for all XModules to either be converted into pure XBlocks or be deleted altogether. Extracting them into separate repositories would be ideal, but even just converting them to pure XBlocks would significantly simplify the runtime.

Glossary
========

More Documentation
==================

`DEPR-24 <https://openedx.atlassian.net/browse/DEPR-24>`_

`Example conversion of Capa <https://github.com/edx/edx-platform/pull/20023/>`_
