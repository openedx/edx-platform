Converting from Require to Webpack
==================================

This guide will help you convert a legacy Require module include to
Webpack. Legacy require modules make use of the mako ``requirejs``
block, which looks like this:

::

    <%block name="requirejs">
        require(["js/factories/myawesomefactory"], function(MyAwesomeFactory) {
            MyAwesomeFactory(${awesome_data | n, dump_js_escaped_json});
        });
    </%block>

This example assumes the following:

- You’re working in Studio (no attempts have been made yet to convert Require
to Webpack in LMS). Studio’s root JS directory is ``/cms/static/js``.
- A factory MyAwesomeFactory invoked from within a Mako template
- MyAwesomeFactory lives in ``/cms/static/js/factories/myawesomefactory.js``
- There’s a contextual Python variable ``awesome_data`` used to populate
``MyAwesomeFactory``.

1. First you’re going to want to create a new ``page`` for your module.
   Add it into the ``cms/static/js/pages`` directory. For example
   purposes, let’s name it ``myawesomepage.js``.

2. Add the following to ``myawesomepage.js``:

::

    define([
        'js/factories/myawesomefactory',
        'common/js/utils/page_factory',
        'js/factories/base',
        'js/pages/course'
    ], function(MyAwesomeFactory, invokePageFactory) {
        'use strict';
        invokePageFactory('MyAwesomeFactory', MyAwesomeFactory);
    }
    );

3. Add a Webpack entry point for ``myawesomepage.js`` in the ``entry``
   object in ``webpack.common.config.js``:

::

    'js/pages/myawesomepage': './cms/static/js/pages/myawesomepage.js',

4. Replace the ``requirejs`` block in your Mako template with a
   ``page_bundle`` block in the following format:

::

    <%block name="page_bundle">
      <%static:invoke_page_bundle page_name="js/pages/myawesomepage" class_name="MyAwesomeFactory">
         ${awesome_page | n, dump_js_escaped_json}
      </%static:invoke_page_bundle>
    </%block>

    Note that we pass the ``awesome_page`` variable into the body of
    ``invoke_page_bundle``. This will ensure `MyAwesomeFactory` has
    access to this data.

5. Run ``paver update_assets`` and make sure everything still works as
   expected. If you run into any build issues, diagnose and fix them.
