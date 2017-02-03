(function(requirejs, define) {
    'use strict';
    // We do not wish to bundle common libraries (that may also be used by non-RequireJS code on the page
    // into the optimized files. Therefore load these libraries through script tags and explicitly define them.
    // Note that when the optimizer executes this code, window will not be defined.
    if (window) {
        var defineDependency = function(globalName, name, noShim) {
            var getGlobalValue = function(name) {
                    var globalNamePath = name.split('.'),
                        result = window,
                        i;
                    for (i = 0; i < globalNamePath.length; i++) {
                        result = result[globalNamePath[i]];
                    }
                    return result;
                },
                globalValue = getGlobalValue(globalName);
            if (globalValue) {
                if (noShim) {
                    define(name, {});
                }
                else {
                    define(name, [], function() { return globalValue; });
                }
            }
            else {
                console.error('Expected library to be included on page, but not found on window object: ' + name);
            }
        };
        defineDependency('jQuery', 'jquery');
        defineDependency('jQuery', 'jquery-migrate');
        defineDependency('_', 'underscore');
    }
    requirejs.config({
        baseUrl: '/base/',
        paths: {
            moment: 'common_static/common/js/vendor/moment-with-locales',
            'draggabilly': 'common_static/js/vendor/draggabilly',
            'edx-ui-toolkit': 'common_static/edx-ui-toolkit'
        },
        'moment': {
            exports: 'moment'
        }
    });
}).call(this, RequireJS.requirejs, RequireJS.define);
