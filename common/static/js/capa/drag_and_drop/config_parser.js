// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return configParser;

    function configParser(state, config) {
        state.config = {
            'draggables': [],
            'baseImage': '',
            'targets': [],
            'onePerTarget': null, // Specified by user. No default.
            'targetOutline': true,
            'labelBgColor': '#d6d6d6',
            'individualTargets': null, // Depends on 'targets'.
            'errors': 0 // Number of errors found while parsing config.
        };

        getDraggables(state, config);
        getBaseImage(state, config);
        getTargets(state, config);
        getOnePerTarget(state, config);
        getTargetOutline(state, config);
        getLabelBgColor(state, config);

        setIndividualTargets(state);

        if (state.config.errors !== 0) {
            return false;
        }

        return true;
    }

    function getDraggables(state, config) {
        if (config.hasOwnProperty('draggables') === false) {
            logme('ERROR: "config" does not have a property "draggables".');
            state.config.errors += 1;
        } else if ($.isArray(config.draggables) === true) {
            (function (i) {
                while (i < config.draggables.length) {
                    if (processDraggable(state, config.draggables[i]) !== true) {
                        state.config.errors += 1;
                    }
                    i += 1;
                }
            }(0));
        } else if ($.isPlainObject(config.draggables) === true) {
            if (processDraggable(state, config.draggables) !== true) {
                state.config.errors += 1;
            }
        } else {
            logme('ERROR: The type of config.draggables is no supported.');
            state.config.errors += 1;
        }
    }

    function getBaseImage(state, config) {
        if (config.hasOwnProperty('base_image') === false) {
            logme('ERROR: "config" does not have a property "base_image".');
            state.config.errors += 1;
        } else if (typeof config.base_image === 'string') {
            state.config.baseImage = config.base_image;
        } else {
            logme('ERROR: Property config.base_image is not of type "string".');
            state.config.errors += 1;
        }
    }

    function getTargets(state, config) {
        if (config.hasOwnProperty('targets') === false) {
            // It is possible that no "targets" were specified. This is not an error.
            // In this case the default value of "[]" (empty array) will be used.
            // Draggables can be positioned anywhere on the image, and the server will
            // get an answer in the form of (x, y) coordinates for each draggable.
        } else if ($.isArray(config.targets) === true) {
            (function (i) {
                while (i < config.targets.length) {
                    if (processTarget(state, config.targets[i]) !== true) {
                        state.config.errors += 1;
                    }
                    i += 1;
                }
            }(0));
        } else if ($.isPlainObject(config.targets) === true) {
            if (processTarget(state, config.targets) !== true) {
                state.config.errors += 1;
            }
        } else {
            logme('ERROR: Property config.targets is not of a supported type.');
            state.config.errors += 1;
        }
    }

    function getOnePerTarget(state, config) {
        if (config.hasOwnProperty('one_per_target') === false) {
            logme('ERROR: "config" does not have a property "one_per_target".');
            state.config.errors += 1;
        } else if (typeof config.one_per_target === 'string') {
            if (config.one_per_target.toLowerCase() === 'true') {
                state.config.onePerTarget = true;
            } else if (config.one_per_target.toLowerCase() === 'false') {
                state.config.onePerTarget = false;
            } else {
                logme('ERROR: Property config.one_per_target can either be "true", or "false".');
                state.config.errors += 1;
            }
        } else {
            logme('ERROR: Property config.one_per_target is not of a supported type.');
            state.config.errors += 1;
        }
    }

    function getTargetOutline(state, config) {
        if (config.hasOwnProperty('target_outline') === false) {
            // It is possible that no "target_outline" was specified. This is not an error.
            // In this case the default value of 'true' (boolean) will be used.
        } else if (typeof config.target_outline === 'string') {
            if (config.target_outline.toLowerCase() === 'true') {
                state.config.targetOutline = true;
            } else if (config.target_outline.toLowerCase() === 'false') {
                state.config.targetOutline = false;
            } else {
                logme('ERROR: Property config.target_outline can either be "true", or "false".');
                state.config.errors += 1;
            }
        } else {
            logme('ERROR: Property config.target_outline is not of a supported type.');
            state.config.errors += 1;
        }
    }

    function getLabelBgColor(state, config) {
        if (config.hasOwnProperty('label_bg_color') === false) {
            // It is possible that no "label_bg_color" was specified. This is not an error.
            // In this case the default value of '#d6d6d6' (string) will be used.
        } else if (typeof config.label_bg_color === 'string') {
            state.config.labelBgColor = config.label_bg_color;
        } else {
            logme('ERROR: Property config.label_bg_color is not of a supported type.');
            returnStatus = false;
        }
    }

    function setIndividualTargets(state) {
        if (state.config.targets.length === 0) {
            state.config.individualTargets = false;
        } else {
            state.config.individualTargets = true;
        }
    }

    function processDraggable(state, obj) {
        if (
            (attrIsString(obj, 'id') === false) ||
            (attrIsString(obj, 'icon') === false) ||
            (attrIsString(obj, 'label') === false) ||

            (attrIsBoolean(obj, 'can_reuse', false) === false)
        ) {
            return false;
        }

        state.config.draggables.push(obj);

        return true;
    }

    function processTarget(state, obj) {
        if (
            (attrIsString(obj, 'id') === false) ||

            (attrIsInteger(obj, 'w') === false) ||
            (attrIsInteger(obj, 'h') === false) ||

            (attrIsInteger(obj, 'x') === false) ||
            (attrIsInteger(obj, 'y') === false)
        ) {
            return false;
        }

        state.config.targets.push(obj);

        return true;
    }

    function attrIsString(obj, attr) {
        if (obj.hasOwnProperty(attr) === false) {
            logme('ERROR: Attribute "obj.' + attr + '" is not present.');

            return false;
        } else if (typeof obj[attr] !== 'string') {
            logme('ERROR: Attribute "obj.' + attr + '" is not a string.');

            return false;
        }

        return true;
    }

    function attrIsInteger(obj, attr) {
        var tempInt;

        if (obj.hasOwnProperty(attr) === false) {
            logme('ERROR: Attribute "obj.' + attr + '" is not present.');

            return false;
        }

        tempInt = parseInt(obj[attr], 10);

        if (isFinite(tempInt) === false) {
            logme('ERROR: Attribute "obj.' + attr + '" is not an integer.');

            return false;
        }

        obj[attr] = tempInt;

        return true;
    }

    function attrIsBoolean(obj, attr, defaultVal) {
        if (obj.hasOwnProperty(attr) === false) {
            if (defaultVal === undefined) {
                logme('ERROR: Attribute "obj.' + attr + '" is not present.');

                return false;
            } else {
                obj[attr] = defaultVal;

                return true;
            }
        }

        if (obj[attr] === '') {
            obj[attr] = defaultVal;
        } else if ((obj[attr] === 'false') || (obj[attr] === false)) {
            obj[attr] = false;
        } else if ((obj[attr] === 'true') || (obj[attr] === true)) {
            obj[attr] = true;
        } else {
            logme('ERROR: Attribute "obj.' + attr + '" is not a boolean.');

            return false;
        }

        return true;
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
