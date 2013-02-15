(function (requirejs, require, define) {

// Bind module.
define(
'videoalpha/display/bind.js',
[],
function () {

    // bind() function.
    return function (fn, me) {
        return function () {
            return fn.apply(me, arguments);
        };
    };

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
// var __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
