// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('GstMain', ['mod1', 'mod2', 'mod3', 'mod4'], function (mod1, mod2, mod3, mod4) {
    return GstMain;

    function GstMain(gstId) {
        console.log('The DOM ID of the current GST element is ' + gstId);
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
