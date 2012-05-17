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

We're using Guard to watch your folder and automatic compile those SASS files.
If you already install all the dependencies using Bundler, you can just do:

    $ bundle exec guard

This will generate the sass file for development which some debugging
information.

### Before Commit

Since this compiled style you're going to push are going to be used on live
production site, you're encouraged to compress all of the style to save some
bandwidth. You can do that by run this command:

    $ bundle exec guard -g production

Guard will watch your directory and generated a compressed version of CSS.
