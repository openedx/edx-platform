## This file is designed to load all the XModule Javascript files in one wad
## using requirejs. It is passed through the Mako template system, which
## populates the `urls` variable with a list of paths to XModule JS files.
## These files assume that several libraries are available and bound to
## variables in the global context, so we load those libraries with requirejs
## and attach them to the global context manually.
define(["jquery", "underscore", "codemirror", "tinymce",
        "jquery.tinymce", "jquery.qtip", "jquery.scrollTo", "jquery.flot",
        "jquery.cookie",
        "utility"],
       function($, _, CodeMirror, tinymce) {
    window.$ = $;
    window._ = _;
    require(['mathjax']);
    window.CodeMirror = CodeMirror;
    window.RequireJS = {
        'requirejs': requirejs,
        'require': require,
        'define': define
    };
    /**
     * Loads all modules one-by-one in exact order.
     * The module should be used until we'll use RequireJS for XModules.
     * @param {Array} modules A list of urls.
     * @return {jQuery Promise}
     **/
    var requireQueue = function(modules) {
        var deferred = $.Deferred();
        var loadScript = function (queue) {
            // Loads the next script if queue is not empty.
            if (queue.length) {
                require([queue.shift()], function() {
                    loadScript(queue);
                });
            } else {
                deferred.resolve();
            }
        };

        loadScript(modules.concat());
        return deferred.promise();
    };

    return requireQueue(${urls});
});
