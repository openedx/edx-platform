**********************************************
LTI module [xmodule]
**********************************************

.. module:: lti_module

Description
===========

The LTI XModule is based on the IMS Global Learning Tools Interoperability
Version 1.1.1 specifications.

Enabling LTI
============

It is not available from the list of general components. To turn it on, add
"lti" to the "advanced_modules" key on the Advanced Settings page.

The module supports 2 modes of operation.

1.) Simple display of external LTI content
2.) display of LTI content that will be graded by external provider

In both cases, before an LTI component from an external provider can be
included in a unit, the following pieces of information must be known/decided
upon:

- LTI id: Internal string representing the external LTI provider. Can be anything.
- Client key: Used for OAuth authentication. Issued by external LTI provider.
- Client secret: Used for OAuth authentication. Issued by external LTI provider.

LTI id is necessary to differentiate between multiple available external LTI
providers that are added to an edX course.

The three fields above must be entered in "lti_passports" field in the format:

[
"{lti_id}:{client_key}:{client_secret}"
]

Multiple external LTI providers are separated by commas:

[
"{lti_id_1}:{client_key_1}:{client_secret_1}",
"{lti_id_2}:{client_key_2}:{client_secret_2}",
"{lti_id_3}:{client_key_3}:{client_secret_3}"
]

Adding LTI to a unit
====================

After LTI has been enabled, and an external provider has been registered, an
instance of it can be added to a unit.

LTI will be available from the Advanced Component category. After adding an LTI
component to a unit, it can be configured by Editing it's settings (the Edit
dialog). The following settings are available:

- Display Name [string]: Title of the new LTI component instance

- custom_parameters: With the "+ Add" button, multiple custom parameters can be
added. Basically, each individual external LTI provider can have a separate
format custom parameters. For example:

key=value

- graded [boolean]: Whether or not this particular LTI instance problem will be
graded by the external LTI provider.

- launch_url [string]: If `rgaded` above is set to `true`, then this must be
the URL that will be passed to the external LTI provider for it to respond with
a grade.

- lti_id [string]: Internal string representing the external LTI provider that
will be used to display content. The same as was entered on the Advanced
Settings page.

- open_in_a_new_page [boolean]: If set to `true`, a link will be present for the student
to click. When the link is clicked, a new window will open with the external
LTI content. If set to `false`, the external LTI content will be loaded in the
page in an iframe.

- weight [float]: If the problem will be graded by an external LTI provider,
the raw grade will be in the range [0.0, 1.0]. In order to change this range,
set the `weight`. The grade that will be stored is calculated by the formula:

stored_grade = raw_grade * weight
