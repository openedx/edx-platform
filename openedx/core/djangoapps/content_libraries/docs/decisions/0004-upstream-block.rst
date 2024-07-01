4. Persist the relationship between blocks and their upstream source
####################################################################

Status
******

Accepted

Pending implementation in (TODO - link)

Context
*******

* TODO - context

Decision
********

* Two new XBlock field types will be introduced:

  * ``NameList`` will hold a flat list of strings that are valid Python names,
    providing streamlined validation and more human-readable OLX than a
    standard JSON-serialized ``List`` field.

    * It will validate that each element is a string matching
      ``[A-Za-z][A-Za-z0-9_]*``
    * It will serialize into a comma-separated list *without* quotation marks
      around values.

  * ``Object`` will hold a key-value mapping, where the keys are a pre-declared
    set of valid Python names, and the values are any valid XBlock field value
    (including Objects themselves).

    * Declaring an object field requires an object with

  will hold a dictionary whose keys are valid Python names,
    providing streamlined validation and more human-readable OLX than a
    standard JSON-serialized ``Dict`` field.

    * Dictionary can be arbitrarily nested.
    * Values are arbitrary.
    *

    providing streamlined validation and more human-readable OLX than a
    standard JSON-serialized ``List`` field.

* The following two fields will be added to every XBlock in CMS:

  .. code-block:: python

     upstream_block = String(
         scope=Scope.settings,
         help=(
             "The usage key of a the block that served as this block's template, if one exists. "
             "Generally, the upstream_block is within a Content Library."
         ),
         hidden=True,
         default=None,
         ...
     )
     upstream_block_version = Integer(
         scope=Scope.settings,
         help=(
             "The upstream_block's version number, at the time this block was created from it. "
             "If this version is older than the upstream_block's latest version, then CMS will "
             "allow this block to fetch updated content from upstream_block."
         ),
         hidden=True,
         default=None,
         ...
     )

* The upstream-defined values of XBlock settings will be exposed in the XBlock API (TODO - details)

* The upstream-defined values will be set when the XBlock is initialized by (TODO - figure this out)

* The existing ``get_block_original_usage`` Modulestore methods will (TODO - figure this out)

* New attributes will be serialized into the OLX of blocks with upstreams:

  * The two new XBlock fields will serialize into OLX as attributes, like any settings-scoped field.
  * The upstream defaults will use a new special syntax: ``upstream.$FIELD_NAME``.
  * The period (``.``) was explicitly chosen to ensure that these special attributes cannot possibly conflict with any Python-defined XBlock fields.

    .. code-block:: xml

       <problem
         display_name="A title that has been customized in the course"
         max_attempts="3"
       >
         <.upstream
            .version=12
            .key="lb:myorg:mylib:problem:p1"
            .overriden="display_name"
            display_name="the title that was defined in the library block"
            max_attempts="3"
         />
         <!-- problem content would go here -->
       </problem>

* Existing LibraryContentBlock children will be missing these attributes, and we will need to handle that (TODO - more details)

Consequences
************

* LibraryContentBlock consequences:

  * Previous ADR (TODO - link) on LibraryContentBlock schema is null and void.
  * Statically-referenced library content will be direct children of the Unit with no LibraryContentBlock wrapper.
  * LibraryContentBlock will only be used for V1 libraries and V2 randomized problem banks.
  * Eventually, we will deprecate V1 libraries and/or port them to V2 randomized problem banks.
  * Long-term, we will remove LibraryContentBlock in favor of a Unit compositor.
  * However, the ``<library_content>`` OLX tag will still be used for randomized content. Would be nice to rename this to ``<randomized>`` ?

* Course-library interaction consequences:

  * Library-defined settings values will now load correctly, whether or not backing library exists. This is good news for courses with library content which need to be imported into different instances.
  * CMS never needs to look up content from older versions of libraries.
  * Library content in courses can now be copy-pasted and duplicated without refreshing from the library. That means that the copy-paste/duplicate operation will copy the blocks as they exist in the course, and later pulling updates down from a library will preserve any student state on those blocks.
  * The slugs of course blocks from libraries can now be set to anything. Previously, they had be meticiulously set so that pulling updates down from the library didn't clobber them.
