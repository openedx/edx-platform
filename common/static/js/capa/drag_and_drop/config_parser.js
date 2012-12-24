// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return configParser;

    function configParser(config, imageDir, state) {
        var returnStatus;

        returnStatus = true;

        state.config = {
            'imageDir': '/static/' + imageDir + '/images/',
            'draggable': [],
            'target': ''
        };

        if ($.isArray(config.draggable) === true) {
            (function (i) {
                while (i < config.draggable.length) {
                    if (processDraggable(config.draggable[i]) !== true) {
                        returnStatus = false;
                    }
                    i += 1;
                }
            }(0));
        } else if ($.isPlainObject(config.draggable) === true) {
            if (processDraggable(config.draggable) !== true) {
                returnStatus = false;
            }
        } else {
            logme('ERROR: The type of config.draggable is no supported.');
            returnStatus = false;
        }

        if (typeof config.target === 'string') {
            state.config.target = config.target;
        } else {
            logme('ERROR: Property config.target is not of type "string".');
            returnStatus = false;
        }

        return true;

        function processDraggable(obj) {
            if (typeof obj.icon !== 'string') {
                logme('ERROR: Attribute "obj.icon" is not a string.');

                return false;
            } else if (typeof obj.label !== 'string') {
                logme('ERROR: Attribute "obj.label" is not a string.');

                return false;
            } else if (typeof obj.name !== 'string') {
                logme('ERROR: Attribute "obj.name" is not a string.');

                return false;
            }

            state.config.draggable.push(obj);

            true;
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
