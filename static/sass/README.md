SASS
====

This project is using Sass to generate its CSS. Sass is a CSS preprocessor that
allows for faster development of CSS. For more information about sass:

   http://sass-lang.com

Install SASS
------------

To use sass, make sure that you have RubyGems install, then you can use Bundler:

    $ gem install bundler
    $ bundle install

This should ensure that you have all the dependencies required for compiling.

Compiling
---------

The dev server will automatically compile sass files that have changed. Simply start
the server using:
    
    $ rake runserver
