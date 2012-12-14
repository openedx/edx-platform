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

        function getParameterValue(paramName) {

            // If the name of the constant is not tracked by state, return an
            // 'undefined' value.
            if (parameters.hasOwnProperty(paramName) === false) {
                return;
            }

            return parameters[paramname].value;
        }

        // ####################################################################
        //
        // Function: setParameterValue(paramName, paramValue, element)
        // --------------------------------------------------
        //
        // This function can be called from a callback, registered by a slider
        // or a text input, when specific events ('slide' or 'change') are
        // triggered.
        //
        // The 'paramName' is the name of the parameter in 'parameters' object
        // whose value must be updated to the new value of 'paramValue'.
        //
        // Before we update the value, we must check that:
        //
        //     1.) the parameter named as 'paramName' actually exists in the
        //         'parameters' object;
        //     2.) the value 'paramValue' is a valid floating-point number, and
        //         it lies within the range specified by the 'min' and 'max'
        //         properties of the stored parameter object.
        //
        // If 'paramName' and 'paramValue' turn out to be valid, we will update
        // the stored value in the parameter with the new value, and also
        // update all of the text inputs and the slider that correspond to this
        // parameter (if any), so that they reflect the new parameter's value.
        //
        // If something went wrong (for example the new value is outside the
        // allowed range), then we will reset the 'element' to display the
        // original value.
        //
        // ####################################################################
        function setParameterValue(paramName, paramValue, element) {
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
        } // End-of: function setParameterValue

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
            var paramName, newParamObj;

            if (typeof obj['@var'] !== 'string') {
                logme(
                    '[ERROR] State.processParameter(obj): obj["@var"] is not a string.',
                    obj['@var'],
                    '---> Not adding a parameter.'
                );

                return;
            }

            paramName = obj['@var'];
            newParamObj = {};

            if (
                (processFloat('@min', 'min') === false) ||
                (processFloat('@max', 'max') === false) ||
                (processFloat('@initial', 'value') === false)
            ) {
                logme('---> Not adding a parameter named "' + paramName + '".');

                return;
            }

            constants[constName] = constValue;

            return;

            function processFloat(attrName, newAttrName) {
                var attrValue;

                if (typeof obj[attrName] !== 'string') {
                    logme(
                        '[ERROR] state.processParameter(obj): obj["' + attrName + '"] is not a string.',
                        obj[attrName]
                    );

                    return false;
                } else {
                    attrValue = parseFloat(obj[attrName]);

                    if (isNaN(attrValue) === true) {
                        logme(
                            '[ERROR] state.processParameter(obj): for attrName = "' + attrName + '" attrValue is NaN.'
                        );

                        return false;
                    }
                }

                newParamObj[newAttrName] = paramValue;

                return true;
            } // End-of: function processFloat
        } // End-of: function processParameter
    } // End-of: function State
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
