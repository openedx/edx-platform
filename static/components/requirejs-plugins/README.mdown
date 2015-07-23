# RequireJS plugins

Small set of plugins for [RequireJS](http://requirejs.org). Some plugins may
also work on other AMD loaders (never tested it).

For more plugins check [RequireJS Wiki](https://github.com/jrburke/requirejs/wiki/Plugins).


## Install

You can use [bower](http://bower.io/) to install it easily:

```
bower install --save requirejs-plugins
```



## Plugins

 - **async** : Useful for JSONP and asynchronous dependencies (e.g. Google Maps).
 - **font** : Load web fonts using the [WebFont Loader API](https://code.google.com/apis/webfonts/docs/webfont_loader.html)
   (requires `propertyParser`)
 - **goog** : Load [Google APIs](http://code.google.com/apis/loader/)
   asynchronously (requires `async!` plugin and `propertyParser`).
 - **image** : Load image files as dependencies. Option to "cache bust".
 - **json** : Load JSON files and parses the result. (Requires `text!` plugin).
 - **mdown** : Load Markdown files and parses into HTML. (Requires `text!`
   plugin and a markdown converter).
 - **noext** : Load scripts without appending ".js" extension, useful for
   dynamic scripts.

### Other

 - **propertyParser** : Just a helper used by some plugins to parse
   arguments (not a real plugin).



## Documentation

check the `examples` folder. All the info you probably need will be inside
comments or on the example code itself.



## Basic usage

Put the plugins inside the `baseUrl` folder (usually same folder as the main.js
file) or create an alias to the plugin location:

```js
require.config({
    paths : {
        //create alias to plugins (not needed if plugins are on the baseUrl)
        async: 'lib/require/async',
        font: 'lib/require/font',
        goog: 'lib/require/goog',
        image: 'lib/require/image',
        json: 'lib/require/json',
        noext: 'lib/require/noext',
        mdown: 'lib/require/mdown',
        propertyParser : 'lib/require/propertyParser',
        markdownConverter : 'lib/Markdown.Converter'
    }
});

//use plugins as if they were at baseUrl
define([
        'image!awsum.jpg',
        'json!data/foo.json',
        'noext!js/bar.php',
        'mdown!data/lorem_ipsum.md',
        'async!http://maps.google.com/maps/api/js?sensor=false',
        'goog!visualization,1,packages:[corechart,geochart]',
        'goog!search,1',
        'font!google,families:[Tangerine,Cantarell]'
    ], function(awsum, foo, bar, loremIpsum){
        //all dependencies are loaded (including gmaps and other google apis)
    }
);
```


## Removing plugin code after build

[r.js](https://github.com/jrburke/r.js/blob/master/build/example.build.js)
nowadays have the `stubModules` setting which can be used to remove the whole
plugin code:

```js
({
    // will remove whole source code of "json" and "text" plugins during build
    // JSON/text files that are bundled during build will still work fine but
    // you won't be able to load JSON/text files dynamically after build
    stubModules : ['json', 'text']
})
```


## Notes about the Markdown plugin

The Markdown plugin was created mainly to be used to compile the markdown files
into HTML during the build step, if you set `pragmasOnSave.excludeMdown=true`
it will remove the `Markdown.Converter.js` and `mdown.js` files from the build.
Example build settings:

```js
({
    baseUrl : './',
    pragmasOnSave : {
        excludeMdown : true
    },
    paths : {
        mdown : 'lib/requirejs/mdown',
        text : 'lib/requirejs/text',
        markdownConverter : 'lib/Markdown.Converter'
    },
    modules : {
        name : 'main'
    }
})
```

If `excludeMdown=true` you won't be able to load markdown files dynamically
after the build.



## Writing your own plugins

Check [RequireJS documentation](http://requirejs.org/docs/plugins.html) for
a basic reference and use other plugins as reference. RequireJS official
plugins are a good source for learning.

Also be sure to check [RequireJS Wiki](https://github.com/jrburke/requirejs/wiki/Plugins).



## Author

[Miller Medeiros](http://blog.millermedeiros.com/)



## License

All the plugins are released under the MIT license.
