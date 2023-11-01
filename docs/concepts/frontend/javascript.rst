JavaScript in edx-platform
==========================

ES2015
------

All new JavaScript code in edx-platform should be written in ES2015.
ES2015 is not a framework or library -- rather, it is the latest and
greatest revision of the JavaScript language itself, natively supported
in all modern browsers and engines. Think of it as JavaScript's
equivalent to Python 3. ES2015 brings with it number of wonderful
syntactic features, such as classes, native imports, arrow functions,
and new data structures. To learn more about ES2015, check out `Luke
Hoban's comprehensive ES6 Features
repo <https://github.com/lukehoban/es6features>`__.

Although ES2015 is natively supported in modern browsers, older browsers
can't interpret it. Here at edX, we support the two latest versions of
every browser, plus IE11, so we need to do a little extra work to
support ES2015. This is where Webpack and Babel come in. Webpack is a
module bundler that transforms, minifies, and compiles frontend code
into pre-built "bundles" to include within pages. It works together with
Babel to transpile ES2015 code into ES5 code, which can safely be used
in all browsers.

Fortunately, you don't need to worry about the gritty details of Webpack
in order to write ES2015 code. You just need to make sure Webpack knows
where to find your files. It's also important to note that **Webpack is
not compatible with RequireJS**. Work is currently underway to move all
legacy RequireJS modules into Webpack, but until it is complete, you
will need to update legacy code yourself in order to use it with ES2015.

Adding a New ES2015 Module
~~~~~~~~~~~~~~~~~~~~~~~~~~

Don't mix ES2015 and ES5 modules within directories. If necessary,
create a new directory just for your new file. If you create a new
directory, run the following from edx-platform root to copy over an
appropriate eslint config:

::

    cp cms/static/js/features_jsx/.eslintrc.js path/to/your/directory

Give your new file an UpperCamelCase filename, such as
``MyAwesomeModule.js``. If it is a React module, use the ``.jsx``
extension; otherwise, use the ``.js`` extension.

If you intend to include this module itself directly within a page, you
will need to tell Webpack about it. Add a line to the ``entry`` object
within ``webpack.common.config.js``.

::

    'MyAwesomeModule': 'path/to/your/directory/MyAwesomeModule.js',

The new entry's key should be the name of your module (typically this is
the same as your filename), and its value should be the path to your
file relative to the edx-platform root.

Writing Your File
~~~~~~~~~~~~~~~~~

Structure your module using ``class``\ es. Typically, you'll want to
define and export one ``class`` per file. If you are going to be
including this module directly within a page and passing it through
Webpack, use a non-default export. ``MyAwesomeModule.js`` should look
something like this:

::

    export class MyAwesomeModule {
      // your awesome code here
    }

Use two-space indentation. This is industry standard practice for
ES2015. If you need to pull in external dependencies, use ``import``
statements:

::

    import moment from 'moment';
    import 'jquery.cookie';
    import { MyOtherModule } from './MyOtherModule';

Building Your File
~~~~~~~~~~~~~~~~~~

Devstack comes with two watcher containers specifically for building
assets. They compile frontend files very quickly, so you can see your
changes reflected in a browser almost immediately. You can run these
containers with:

::

    make dev.up.watchers

and stop them with

::

    make stop.watchers

If you make any changes to ``webpack.common.config.js`` while the
watchers are running, you will need to restart the watchers in order for
them to pick up your changes.

If your changes aren't being reflected in the browser, check the logs
with ``make logs`` to see if something went wrong. If you get stuck, ask
for help in the FedX hipchat room, or in #front-end on Slack.
