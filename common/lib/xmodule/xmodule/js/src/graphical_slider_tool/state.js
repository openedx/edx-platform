// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('State', ['logme'], function (logme) {
    // Since there will be (can be) multiple GST on a page, and each will have
    // a separate state, we will create a factory constructor function. The
    // constructor will expect the ID of the DIV with the GST contents, and the
    // configuration object (parsed from a JSON string). It will return and
    // object containing methods to set and get the private state properties.

    // This module defines and returns a factory constructor.
    return State;

    // function: State
    function State(gstId, config) {
        var parameters, allParameterNames, allParameterValues, plotDiv;

        parameters = {};

        if (
            (typeof config.parameters !== 'undefined') &&
            (typeof config.parameters.param !== 'undefined')
        ) {

            // If config.parameters.param is an array, pass it to the processor
            // element by element.
            if ($.isArray(config.parameters.param) === true) {
                (function (c1) {
                    while (c1 < config.parameters.param.length) {
                        addConstFromInput(config.parameters.param[c1]);
                        c1 += 1;
                    }
                }(0));
            }

            // If config.parameters.param is an object, pass this object to the
            // processor directly.
            else if ($.isPlainObject(config.inputs.input) === true) {
                addConstFromInput(config.parameters.param);
            }

        }

        // The constructor will return an object with methods to operate on
        // it's private properties.
        return {
            'getParameterValue': getParameterValue,
            'setParameterValue': setParameterValue,

            'getAllParameterNames': getAllParameterNames,
            'getAllParameterValues': getAllParameterValues,

            'bindUpdatePlotEvent': bindUpdatePlotEvent
        };

        // ####################################################################
        //
        // To get all parameter names, you would do:
        //
        //     allParamNames = getAllParameterProperties('name');
        //
        // To get all parameter values, you would do:
        //
        //     allParamValues = getAllParameterProperties('value');
        //
        // ####################################################################
        function getAllParameterProperties(propertyName) {
            var paramName, allParamProperties;

            allParamProperties = [];

            for (paramName in parameters) {
                allParamProperties.push(parameters[paramName][propertyName]);
            }

            return allParamProperties;
        }

        function bindUpdatePlotEvent(newPlotDiv, callback) {
            plotDiv = newPlotDiv;

            plotDiv.bind('update_plot', callback);
        }

        function getParameterValue(constName) {


            if (constants.hasOwnProperty(constName) === false) {
                // If the name of the constant is not tracked by state, return an
                // 'undefined' value.
                return;
            }

            return constants[constName];
        }

        function setConstValue(constName, constValue) {
            var inputDiv;

            if (constants.hasOwnProperty(constName) === false) {
                // If the name of the constant is not tracked by state, return an
                // 'undefined' value.
                return;
            }

            if (isNaN(parseFloat(constValue)) === true) {
                // We are interested only in valid float values.
                return;
            }

            constants[constName] = parseFloat(constValue);

            if (plotDiv !== undefined) {
                plotDiv.trigger('update_plot');
            }

            inputDiv = $('#' + gstId + '_input_' + constName).children('input');
            if (inputDiv.length !== 0) {
                inputDiv.val(constValue);
            }
        }

        // ####################################################################
        //
        // Function: processParameter(obj)
        // -------------------------------
        //
        //
        // This function will be run once for each instance of a GST.
        //
        // 'newParamObj' must be empty from the start for each invocation of
        // this function, that's why we will declare it locally.
        //
        // We will parse the passed object 'obj' and populate the 'newParamObj'
        // object with required properties.
        //
        // Since there will be many properties that are of type floating-point
        // number, we will have a separate function for parsing them.
        //
        // processParameter() will fail right away if 'obj' does not have a
        // '@var' property which represents the name of the parameter we want
        // to process.
        //
        // If, after all of the properties have been processed, we reached the
        // end of the function successfully, the 'newParamObj' will be added to
        // the 'parameters' object (that is defined in the scope of State()
        // function) as a property named as the name of the parameter.
        //
        // If at least one of the properties from 'obj' does not get correctly
        // parsed, then the parameter represented by 'obj' will be disregarded.
        // It will not be available to user-defined plotting functions, and
        // things will most likely break. We will notify the user about this.
        //
        // ####################################################################
        function processParameter(obj) {
            var newParamObj;

            if (typeof obj['@var'] !== 'string') {
                logme(
                    '[ERROR] state.processParameter(obj): obj["' + attrName + '"] is not a string.'
                );
            }

            newParamObj = {};

            processString('@var', 'name');

            processFloat('@min', 'min');
            processFloat('@max', 'max');
            processFloat('@initial', 'value');

            if (checkRequired('name', 'min', 'max', 'value') === false) {
                logme('Not creating a parameter.');
                return;
            }


            constants[constName] = constValue;

            return;

            function processFloat(attrName, newAttrName) {
                var attrValue;

                if (typeof obj[attrName] !== 'string') {
                    logme(
                        '[ERROR] state.processParameter(obj): obj["' + attrName + '"] is not a string.'
                    );

                    return;
                } else {
                    attrValue = parseFloat(obj[attrName]);

                    if (isNaN(attrValue) === true) {
                        logme(
                            '[ERROR] state.processParameter(obj): for attrName = "' + attrName + '" attrValue is NaN.'
                        );

                        return;
                    }
                }

                newParamObj[newAttrName] = paramValue;
            }

            function processString(attrName, newAttrName) {
                if (typeof obj[attrName] !== 'string') {
                    logme(
                        '[ERROR] state.processParameter(obj): obj["' + attrName + '"] is not a string.'
                    );

                    return;
                }

                newParamObj[newAttrName] = obj[attrName];
            }
        }

        function addConstFromSlider(obj) {
            var constName, constValue, rangeBlobs;

            // The name of the constant is obj['@var']. The value (initial) of
            // the constant is the second blob of the 'range' parameter of the
            // slider which is obj['@range']. Multiple sliders and/or inputs
            // can represent the same constant - therefore 'initial' is in
            // brackets. The range is a string composed of 3 blobs, separated
            // by commas.

            if (typeof obj['@var'] === 'undefined') {
                return;
            }

            constName = obj['@var'];

            if (typeof obj['@range'] !== 'string') {
                constValue = 0;
            } else {
                rangeBlobs = obj['@range'].split(',');

                // We must have gotten exactly 3 blobs (pieces) from the split.
                if (rangeBlobs.length !== 3) {
                    constValue = 0;
                } else {
                    // Get the second blob from the split string.
                    constValue = parseFloat(rangeBlobs[1]);

                    if (isNaN(constValue) === true) {
                        constValue = 0;
                    }
                }
            }

            constants[constName] = constValue;
        }
    } // End-of: function State
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
