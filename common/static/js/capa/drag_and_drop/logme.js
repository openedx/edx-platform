(function (requirejs, require, define) {
define([], function () {
    var debugMode;

    debugMode = true;

    return logme;

    function logme() {
        var i;

        if (
            (debugMode !== true) ||
            (typeof window.console === 'undefined')
        ) {
            return;
        }

        i = 0;
        while (i < arguments.length) {
            window.console.log(arguments[i]);
            i += 1;
        }
    }
}); // End-of: define([], function () {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define) {
