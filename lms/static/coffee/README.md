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

CoffeeScript is compiled when you update assets using the command:

    $ paver update_assets

Testing
-------

We use Jasmine to unit-test the JavaScript files.  See `docs/en_us/internal/testing.rst` for details.
