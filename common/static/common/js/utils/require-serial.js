/*
Helper function used to require files serially instead of concurrently.
 */
(function(window, require) {
    'use strict';

    var requireModules = function(paths, callback, modules) {
        // If all the modules have been loaded, call the callback.
        if (paths.length === 0) {
            return callback.apply(null, modules);
        }
        // Otherwise load the next one.
        require([paths.shift()], function(module) {
            modules.push(module);
            requireModules(paths, callback, modules);
        });
    };

    window.requireSerial = function(paths, callback) {
        requireModules(paths, callback, []);
    };
}).call(this, window, require || RequireJS.require);
