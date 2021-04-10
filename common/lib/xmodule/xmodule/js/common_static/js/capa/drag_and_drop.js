// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://openedx.atlassian.net/wiki/display/PLAT/Integration+of+Require+JS+into+the+system
(function(requirejs, require, define) {
// HACK: this should be removed when it is safe to do so
    if (window.baseUrl) {
        requirejs.config({baseUrl: baseUrl});
    }

// The current JS file will be loaded and run each time. It will require a
// single dependency which will be loaded and stored by RequireJS. On
// subsequent runs, RequireJS will return the dependency from memory, rather
// than loading it again from the server. For that reason, it is a good idea to
// keep the current JS file as small as possible, and move everything else into
// RequireJS module dependencies.
    require(['js/capa/drag_and_drop/main'], function(Main) {
        Main();
    });

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
