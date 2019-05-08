Status: Maintenance

Responsibilities
================
The Experiments django app provides a generic API and schema-less data model for storing data related to experiments. It contains both user-specific and user-agnostic key-value stores that can be associated with experiments. The mapping between an experiment and its experiment_id is maintained externally to the code, as it is specific to the Open edX instance.

WARNING: Do NOT use this app for storing long-term data. The data in this app is intended to be transitional and deleted once experiments are completed.

Direction: Keep
===============

Glossary
========

More Documentation
==================
