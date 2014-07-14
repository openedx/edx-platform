## This file is designed to load all the XModule Javascript files in one wad
## using requirejs. It is passed through the Mako template system, which
## populates the `urls` variable with a list of paths to XModule JS files.
## These files assume that several libraries are available and bound to
## variables in the global context, so we load those libraries with requirejs
## and attach them to the global context manually.
define(["jquery", "underscore", "mathjax", "codemirror", "tinymce",
        "jquery.tinymce", "jquery.qtip", "jquery.scrollTo", "jquery.flot",
        "jquery.cookie",
        "utility"],
       function($, _, MathJax, CodeMirror, tinymce) {
    window.$ = $;
    window._ = _;
    window.MathJax = MathJax;
    window.CodeMirror = CodeMirror;
    window.RequireJS = {
        'requirejs': requirejs,
        'require': require,
        'define': define
    };

    var urls = ${urls};
    var head = $("head");
    var deferred = $.Deferred();
    var numResources = urls.length;
    $.each(urls, function (i, url) {
        head.append($("<script/>", {src: url}));
        // Wait for all the scripts to execute.
        require([url], function () {
            if (i === numResources - 1) {
               deferred.resolve();
            }
        });
    });

    return deferred.promise();
});
