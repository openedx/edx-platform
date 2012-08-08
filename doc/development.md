# Running the CMS

One can start the CMS by running `rake cms`. This will run the server on localhost
port 8001.

However, the server also needs data to work from.

## Installing Mongodb

Please see http://www.mongodb.org/downloads for more detailed instructions.

### Ubuntu

    sudo apt-get install mongodb

### OSX

Use the MacPorts package `mongodb` or the Homebrew formula `mongodb`

## Initializing Mongodb

Check out the course data directories that you want to work with into the
`GITHUB_REPO_ROOT` (by default, `../data`). Then run the following command:


    rake django-admin[import,cms,dev,../data]

Replace `../data` with your `GITHUB_REPO_ROOT` if it's not the default value.

This will import all courses in your data directory into mongodb

## Unit tests

This runs all the tests (long, uses collectstatic):

    rake test
    
xmodule can be tested independently, with this:

    rake test_common/lib/xmodule
    
To see all available rake commands, do this:

    rake -T
    