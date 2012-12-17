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
    function State(gstId, gstClass, config) {
        var parameters, allParameterNames, allParameterValues,
            plotDiv;

        // Initially, there are no parameters to track. So, we will instantiate
        // an empty object.
        //
        // As we parse the JSON config object, we will add parameters as
        // named properties (for example
        //
        //     parameters.a = {...};
        //
        // for the parameter 'a'.
        parameters = {};

        // Check that the required object is available.
        if (
            (typeof config.parameters !== 'undefined') &&
            (typeof config.parameters.param !== 'undefined')
        ) {

            // If config.parameters.param is an array, pass it to the processor
            // element by element.
            if ($.isArray(config.parameters.param) === true) {
                (function (c1) {
                    while (c1 < config.parameters.param.length) {
                        processParameter(config.parameters.param[c1]);
                        c1 += 1;
                    }
                }(0));
            }

            // If config.parameters.param is an object, pass this object to the
            // processor directly.
            else if ($.isPlainObject(config.inputs.input) === true) {
                processParameter(config.parameters.param);
            }

        }

        // Instead of building these arrays every time when some component
        // requests them, we will create them in the beginning, and then update
        // by element when some parameter's value changes.
        //
        // Then we can just return the required array, instead of iterating
        // over all of the properties of the 'parameters' object, and
        // extracting their names/values one by one.
        allParameterNames = [];
        allParameterValues = [];

        generateHelperArrays();

        logme(parameters, allParameterNames, allParameterValues);

        // The constructor will return an object with methods to operate on
        // it's private properties.
        return {
            'getParameterValue': getParameterValue,
            'setParameterValue': setParameterValue,

            'getParamObj': getParamObj,

            'getAllParameterNames': getAllParameterNames,
            'getAllParameterValues': getAllParameterValues,

            'bindUpdatePlotEvent': bindUpdatePlotEvent
        };

        function getAllParameterNames() {
            return allParameterNames;
        }

        function getAllParameterValues() {
            return allParameterValues;
        }

        function getParamObj(paramName) {
            if (parameters.hasOwnProperty(paramName) === false) {
                return;
            }

            return parameters[paramName];
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
        // Finally, the helper array 'allParameterValues' will also be updated
        // to reflect the change.
        //
        // If something went wrong (for example the new value is outside the
        // allowed range), then we will reset the 'element' to display the
        // original value.
        //
        // ####################################################################
        function setParameterValue(paramName, paramValue, element) {
            var paramValueNum, c1;

            // If a parameter with the name specified by the 'paramName'
            // parameter is not tracked by state, do not do anything.
            if (parameters.hasOwnProperty(paramName) === false) {
                return;
            }

            // Try to convert the passed value to a valid floating-point
            // number.
            paramValueNum = parseFloat(paramValue);

            if (
                // We are interested only in valid float values. NaN, -INF,
                // +INF we will disregard.
                (isFinite(paramValueNum) === false) ||

                // If the new parameter's value is valid, but lies outised of
                // the parameter's allowed range, we will also disregard it.
                (paramValueNum < parameters[paramName].min) ||
                (paramValueNum > parameters[paramName].max)
            ) {
                // We will also change the element's value back to the current
                // parameter's value.
                element.val(parameters[paramName].value);

                return;
            }

            parameters[paramName].value = paramValueNum;

            if (plotDiv !== undefined) {
                plotDiv.trigger('update_plot');
            }

            for (c1 = 0; c1 < parameters[paramName].inputDivs.length; c1 += 1) {
                parameters[paramName].inputDivs[c1].val(paramValueNum);
            }

            if (parameters[paramName].sliderDiv !== null) {
                parameters[paramName].sliderDiv.slider('value', paramValueNum);
            }

            allParameterValues[parameters[paramName].helperArrayIndex] = paramValueNum;
        } // End-of: function setParameterValue

        // ####################################################################
        //
        // Function: processParameter(obj)
        // -------------------------------
        //
        //
        // This function will be run once for each instance of a GST when
        // parsing the JSON config object.
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
                (processFloat('@step', 'step') === false) ||
                (processFloat('@initial', 'value') === false)
            ) {
                logme('---> Not adding a parameter named "' + paramName + '".');

                return;
            }

            newParamObj.inputDivs = [];
            newParamObj.sliderDiv = null;

            parameters[paramName] = newParamObj;

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

                newParamObj[newAttrName] = attrValue;

                return true;
            } // End-of: function processFloat
        } // End-of: function processParameter

        // Populate 'allParameterNames' and 'allParameterValues' with data.
        // Link each parameter object with the corresponding helper array via
        // an index ('helperArrayIndex'). It will be the same for both of the
        // arrays.
        function generateHelperArrays() {
            var paramName, c1;

            c1 = 0;
            for (paramName in parameters) {
                allParameterNames.push(paramName);
                allParameterValues.push(parameters[paramName].value);

                parameters[paramName].helperArrayIndex = c1;

                c1 += 1;
            }
        }
    } // End-of: function State
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
