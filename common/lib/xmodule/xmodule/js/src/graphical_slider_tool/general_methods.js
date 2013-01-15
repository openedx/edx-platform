// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('GeneralMethods', [], function () {
    if (!String.prototype.trim) {
        // http://blog.stevenlevithan.com/archives/faster-trim-javascript
        String.prototype.trim = function trim(str) {
            return str.replace(/^\s\s*/, '').replace(/\s\s*$/, '');
        };
    }

    return {
        'module_name': 'GeneralMethods',
        'module_status': 'OK'
    };
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
