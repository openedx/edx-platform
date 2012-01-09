This project is using Sass to generate it's CSS. Sass is a CSS preprocessor that allows for faster development of CSS. For more information about sass: http://sass-lang.com

To use sass all you need to do is enter:
$ gem install sass

We are also using Bourbon with sass. They are a generic set of mixins, and functions that allow for more rapid development of CSS3. Find out more about bourbon here: https://github.com/thoughtbot/bourbon

Then to generate Sass files cd to templates directory and watch the sass files with: 
$ sass --watch sass:../static/css/ -r ./sass/bourbon/lib/bourbon.rb

This will automatically generate the CSS files on save.
