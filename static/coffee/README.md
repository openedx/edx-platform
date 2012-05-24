CoffeeScript
============

This folder contains the CoffeeScript file that will be compiled to the static
directory. By default, we're compile and merge all the files ending `.coffee`
into `static/js/application.js`.

Install the Compiler
--------------------

CoffeeScript compiler are written in JavaScript. You'll need to install Node and
npm (Node Package Manager) to be able to install the CoffeeScript compiler.

### Mac OS X

Install Node via Homebrew, then use npm:

    $ brew install node
    $ curl http://npmjs.org/install.sh | sh
    $ npm install -g git://github.com/jashkenas/coffee-script.git

(Note that we're using the edge version of CoffeeScript for now, as there was
some issue with directory watching in 1.3.1.)

Try to run `coffee` and make sure you get a coffee prompt.

### Debian/Ubuntu

Conveniently, you can install Node via `apt-get`, then use npm:

    $ sudo apt-get install nodejs npm &&
    $ sudo npm install -g git://github.com/jashkenas/coffee-script.git

Compiling
---------

The dev server will automatically compile coffeescript files that have changed.
Simply start the server using:
    
    $ rake runserver

Testing
-------

We're also using Jasmine to unit-testing the JavaScript files. All the specs are
written in CoffeeScript for the consistency. To access the test cases, start the
server in debug mode, navigate to http://127.0.0.1:8000/_jasmine to see the
test result.
