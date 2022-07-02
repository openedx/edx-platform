/**
 * An AMD loader that installs modules into the global edx namespace.
 *
 * @module GlobalLoader
 */
/* global $, _ */
(function() {
    'use strict';

    window.edx = window.edx || {};

    window.edx.GlobalLoader = (function() {
        var registeredModules = {},
            GlobalLoader;

        // Register standard libraries
        registeredModules.jquery = $;
        registeredModules.underscore = _;

        GlobalLoader = {
            /**
             * Define a module that can be accessed globally in the edx namespace.
             *
             * This function will typically be used in situations where UI Toolkit
             * functionally is needed in code where RequireJS is not available.
             * The module definition should be wrapped in boilerplate as follows:
             *
             *~~~ javascript
             * ;(function(define) {
             *     'use strict';
             *     define([...], function(...) {
             *         ...
             *     });
             * }).call(
             *     this,
             *     // Pick a define function as follows:
             *     // 1. Use the default 'define' function if it is available
             *     // 2. If not, use 'RequireJS.define' if that is available
             *     // 3. else use the GlobalLoader to install the class into the edx namespace
             *     typeof define === 'function' && define.amd ? define :
             *         (typeof RequireJS !== 'undefined' ? RequireJS.define :
             *             edx.GlobalLoader.defineAs('ModuleName', 'PATH/TO/MODULE'))
             * );
             *~~~
             * @param {string} name The name by which the module will be accessed.
             * @param {string} path The module's path.
             * @returns {Function} A function that will create the module.
             */
            defineAs: function(name, path) {
                return function(requiredPaths, moduleFunction) {
                    var requiredModules = [],
                        pathCount = requiredPaths.length,
                        requiredModule,
                        module,
                        i;
                    for (i = 0; i < pathCount; i += 1) {
                        requiredModule = registeredModules[requiredPaths[i]];
                        requiredModules.push(requiredModule);
                    }
                    module = moduleFunction.apply(GlobalLoader, requiredModules);
                    registeredModules[path] = module;
                    edx[name] = module;
                };
            },

            /**
             * Clears all registered modules.
             *
             * Note: this function is only provided for unit testing.
             */
            clear: function() {
                registeredModules = {};
            }
        };

        return GlobalLoader;
    }());
}).call(this);
