2. Storage and serialization of Blockstore-based library content
----------------------------------------------------------------

Status
======

Draft


Context
=======

TODO


Decision
========

Data model of the library_content_v2 Block
******************************************

*Note: There exists a ``library_sourced`` implementation live on stage.edx.org. This ADR proposes to rename and modify it.*

We will implement a ``library_content_v2`` XBlock type. It will allow course authors to pick a set of blocks from one or more V2 content libraries. The selected blocks shall be rendered within the views methods of the ``library_content_v2`` block. This will enable the inclusion of Blockstore-based library content into Modulestore-based course runs.

(We may also implement other XBlock types to allow content randomization or other special patterns of including Blockstore-based library content into Modulestore. These XBlock type(s) will likely share much of the logic described below for ``library_content_v2``.)

The block will have a field called ``source_libraries``.  This will be a list of library locators with associated version information. The version will be a hash of the contents of the specific library version (the significance of this will be dicussed later).

The block will also have a field called ``library_blocks``. This will be a list of library block usage locators *without* associated version information.

Finally, the block will have fields ``field_overrides`` and ``block_field_overrides``. The former stores field overrides that are applied to all sourced blocks, whereas the latter stores field overrides for specific blocks. The specific mechanism by which field overrides are instrumented is to be determined.

Example (pseudo-data):

.. code-block:: JSON

  {
    "type": "library_content_v2",
    "fields": {
      "source_libraries": [
        "lib:ScienceX:ChemLib1:377f199e1da...",
        "lib:EngineeringX:BasicChemLib:6bab2d2d22..."
      ],
      "library_blocks": [
        "lb:ScienceX:ChemLib1:problem:mc1",
        "lb:EngineeringX:BasicChemLib:video:stiochiometry",
        "lb:ScienceX:ChemLib1:problem:mc2",
      ],
      "field_overrides": [
        "weight": 0.5
      ],
      "block_field_overrides": {
        "lb:EngineeringX:BasicChemLib:video:stoichiometry": {
          "display_name": "How to Stoichiometry"
        }
      }
    }
  }

Accessing library-sourced blocks
********************************

Although the ``library_content_v2`` block described above stores references to libraries and library block usages, the content of the library-sourced blocks themselves would not be imported into in modulestore. Instead, their definitions would remain authoritatively within blockstore bundles. When rendering Studio-facing XBlock views, Studio would query blockstore for the requisite block OLX, deserialize it, and instantiate the block.

We will also build an LMS-specific store for library blocks. When a blockstore content library is published, updated versions of the library blocks will be pushed into LMS. This store will be optimized specifically for the high-read LMS use case. It will be persisted so that if Studio/blockstore is unavailable, content can still be accessed by LMS.

With this approach, we avoid having to copy blockstore library content to modulestore.


Contextual block usage keys
***************************

The decision not to store library-sourced blocks in modulestore begs the question of what keys will be used to reference them.

Content within the course run hierarchy is traditionally assigned a usage key of the form ``course-v1:ORG+COURSE+RUN+type@TYPE+block@USAGE_ID``. Since these library-sourced blocks are not stored along with the course run hierarchy in the normal way, though, I am not sure if this is appropriate.

However, it is essential that library-sourced blocks usages are unambigously addressable. We cannot assume that a single library block will only be used in a course once; therefore, the library block usage keys of the form ``lb:ORG:LIBRARY:TYPE:ID`` are also not viable.

Instead, we will introduce a new key namespace ``cb:``, roughly standing for either "course run block" or "contextual block". It will uniquely identify a usage of a defined block within a learning context. (The namespace was chosen to be analogous with ``lb:``, which identifies block definitions within blockstore content libraries.)

A contextual block usage key will take the form::

  cb::USAGE_CONTEXT::BLOCK_ID

For example, if the stoichiometry video above were included in a ScienceX course run, its
usage key would be look like::

  cb::block-v1:ScienceX+Chem+101+2024+type@library_content+block@abcd1234::lb:EngineeringX:BasicChemLib:video:stoichiometry

  clb:block-v1:ScienceX+Chem+101+2024+type@library_content+block@abcd1234:EngineeringX:BasicChemLib:video:stoichiometry

Note that the usage context here is not just the course run key, but instead is of the usage key of
``library_content_v2`` block that includes the stoichiometry video.

This idea is intended to be forward-compatible with blockstore-based courses, which will be built of blocks identified by ``cb:`` keys::

  clb:ScienceX:Chem101_2024:library_content_v2:abcd1234:EngineeringX:BasicChemLib:video:stoichiometry


Serializing for OLX Export
**************************

TODO


Deserlization from OLX Import
*****************************

TODO

Consequences
============

TODO
