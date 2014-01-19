// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('State', [], function () {
    var stateInst;

    // Since there will be (can be) multiple GST on a page, and each will have
    // a separate state, we will create a factory constructor function. The
    // constructor will expect the ID of the DIV with the GST contents, and the
    // configuration object (parsed from a JSON string). It will return an
    // object containing methods to set and get the private state properties.

    stateInst = 0;

    // This module defines and returns a factory constructor.
    return State;

    function State(gstId, config) {
        var parameters, allParameterNames, allParameterValues,
            plotDiv, dynamicEl, dynamicElByElId;

        dynamicEl = [];
        dynamicElByElId = {};

        stateInst += 1;
        // console.log('MESSAGE: Creating state instance # ' + stateInst + '.');

        // Initially, there are no parameters to track. So, we will instantiate
        // an empty object.
        //
        // As we parse the JSON config object, we will add parameters as
        // named properties. For example
        //
        //     parameters.a = {...};
        //
        // will be created for the parameter 'a'.
        parameters = {};

        // Check that the required parameters config object is available.
        if ($.isPlainObject(config.parameters) === false) {
            console.log('ERROR: Expected config.parameters to be an object. It is not.');
            console.log('config.parameters = ', config.parameters);

            return;
        }

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
        else if ($.isPlainObject(config.parameters.param) === true) {
            processParameter(config.parameters.param);
        }

        // If config.parameters.param is some other type, report an error and
        // do not continue.
        else {
            console.log('ERROR: config.parameters.param is of an unsupported type.');
            console.log('config.parameters.param = ', config.parameters.param);

            return;
        }

        // Instead of building these arrays every time when some component
        // requests them, we will create them in the beginning, and then update
        // each element individually when some parameter's value changes.
        //
        // Then we can just return the required array, instead of iterating
        // over all of the properties of the 'parameters' object, and
        // extracting their names/values one by one.
        allParameterNames = [];
        allParameterValues = [];

        // Populate 'allParameterNames', and 'allParameterValues' with data.
        generateHelperArrays();

        // The constructor will return an object with methods to operate on
        // it's private properties.
        return {
            'getParameterValue': getParameterValue,
            'setParameterValue': setParameterValue,

            'getParamObj': getParamObj,

            'getAllParameterNames': getAllParameterNames,
            'getAllParameterValues': getAllParameterValues,

            'bindUpdatePlotEvent': bindUpdatePlotEvent,
            'addDynamicEl': addDynamicEl,

            // plde is an abbreviation for Plot Label Dynamic Elements.
            plde: []
        };

        function getAllParameterNames() {
            return allParameterNames;
        }

        function getAllParameterValues() {
            return allParameterValues;
        }

        function getParamObj(paramName) {
            if (parameters.hasOwnProperty(paramName) === false) {
                console.log('ERROR: Object parameters does not have a property named "' + paramName + '".');

                return;
            }

            return parameters[paramName];
        }

        function bindUpdatePlotEvent(newPlotDiv, callback) {
            plotDiv = newPlotDiv;

            plotDiv.bind('update_plot', callback);
        }

        function addDynamicEl(el, func, elId, updateOnEvent) {
            var newLength;

            newLength = dynamicEl.push({
                'el': el,
                'func': func,
                'elId': elId,
                'updateOnEvent': updateOnEvent
            });

            if (typeof dynamicElByElId[elId] !== 'undefined') {
                console.log(
                    'ERROR: Duplicate dynamic element ID "' + elId + '" found.'
                );
            } else {
                dynamicElByElId[elId] = dynamicEl[newLength - 1];
            }
        }

        function getParameterValue(paramName) {

            // If the name of the constant is not tracked by state, return an
            // 'undefined' value.
            if (parameters.hasOwnProperty(paramName) === false) {
                console.log('ERROR: Object parameters does not have a property named "' + paramName + '".');

                return;
            }

            return parameters[paramname].value;
        }

        // ####################################################################
        //
        // Function: setParameterValue(paramName, paramValue, element)
        // --------------------------------------------------
        //
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
        function setParameterValue(paramName, paramValue, element, slider, updateOnEvent) {
            var paramValueNum, c1;

            // If a parameter with the name specified by the 'paramName'
            // parameter is not tracked by state, do not do anything.
            if (parameters.hasOwnProperty(paramName) === false) {
                console.log('ERROR: Object parameters does not have a property named "' + paramName + '".');

                return;
            }

            // Try to convert the passed value to a valid floating-point
            // number.
            paramValueNum = parseFloat(paramValue);

            // We are interested only in valid float values. NaN, -INF,
            // +INF we will disregard.
            if (isFinite(paramValueNum) === false) {
                console.log('ERROR: New parameter value is not a floating-point number.');
                console.log('paramValue = ', paramValue);

                return;
            }

            if (paramValueNum < parameters[paramName].min) {
                paramValueNum = parameters[paramName].min;
            } else if (paramValueNum > parameters[paramName].max) {
                paramValueNum = parameters[paramName].max;
            }

            parameters[paramName].value = paramValueNum;

            // Update all text inputs with the new parameter's value.
            for (c1 = 0; c1 < parameters[paramName].inputDivs.length; c1 += 1) {
                parameters[paramName].inputDivs[c1].val(paramValueNum);
            }

            // Update the single slider with the new parameter's value.
            if ((slider === false) && (parameters[paramName].sliderDiv !== null)) {
                parameters[paramName].sliderDiv.slider('value', paramValueNum);
            }

            // Update the helper array with the new parameter's value.
            allParameterValues[parameters[paramName].helperArrayIndex] = paramValueNum;

            for (c1 = 0; c1 < dynamicEl.length; c1++) {
                if (
                    ((updateOnEvent !== undefined) && (dynamicEl[c1].updateOnEvent === updateOnEvent)) ||
                    (updateOnEvent === undefined)
                ) {
                    // If we have a DOM element, call the function "paste" the answer into the DIV.
                    if (dynamicEl[c1].el !== null) {
                        dynamicEl[c1].el.html(dynamicEl[c1].func.apply(window, allParameterValues));
                    }
                    // If we DO NOT have an element, simply call the function. The function can then
                    // manipulate all the DOM elements it wants, without the fear of them being overwritten
                    // by us afterwards.
                    else {
                        dynamicEl[c1].func.apply(window, allParameterValues);
                    }
                }
            }

            // If we have a plot DIV to work with, tell to update.
            if (plotDiv !== undefined) {
                plotDiv.trigger('update_plot');
            }

            return true;
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
                console.log('ERROR: Expected obj["@var"] to be a string. It is not.');
                console.log('obj["@var"] = ', obj['@var']);

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
                console.log('ERROR: A required property is missing. Not creating parameter "' + paramName + '"');

                return;
            }

            // Pointers to text input and slider DIV elements that this
            // parameter will be attached to. Initially there are none. When we
            // will create text inputs and sliders, we will update these
            // properties.
            newParamObj.inputDivs = [];
            newParamObj.sliderDiv = null;

            // Everything went well, so save the new parameter object.
            parameters[paramName] = newParamObj;

            return;

            function processFloat(attrName, newAttrName) {
                var attrValue;

                if (typeof obj[attrName] !== 'string') {
                    console.log('ERROR: Expected obj["' + attrName + '"] to be a string. It is not.');
                    console.log('obj["' + attrName + '"] = ', obj[attrName]);

                    return false;
                } else {
                    attrValue = parseFloat(obj[attrName]);

                    if (isFinite(attrValue) === false) {
                        console.log('ERROR: Expected obj["' + attrName + '"] to be a valid floating-point number. It is not.');
                        console.log('obj["' + attrName + '"] = ', obj[attrName]);

                        return false;
                    }
                }

                newParamObj[newAttrName] = attrValue;

                return true;
            } // End-of: function processFloat
        } // End-of: function processParameter

        // ####################################################################
        //
        // Function: generateHelperArrays()
        // -------------------------------
        //
        //
        // Populate 'allParameterNames' and 'allParameterValues' with data.
        // Link each parameter object with the corresponding helper array via
        // an index 'helperArrayIndex'. It will be the same for both of the
        // arrays.
        //
        // NOTE: It is important to remember to update these helper arrays
        // whenever a new parameter is added (or one is removed), or when a
        // parameter's value changes.
        //
        // ####################################################################
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
