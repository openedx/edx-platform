// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('State', [], function () {
    // Since there will be (can be) multiple GST on a page, and each will have
    // a separate state, we will create a factory constructor function. The
    // constructor will expect the ID of the DIV with the GST contents, and the
    // configuration object (parsed from a JSON string). It will return and
    // object containing methods to set and get the private state properties.

    // This module defines and returns a factory constructor.
    return State;

    /*
     * function: State
     *
     *
     */
    function State(gstId, config) {
        var constants, c1, plotDiv;

        constants = {};

        // We must go through all of the input, and slider elements and
        // retrieve all of the available constants. These will be added to an
        // object as it's properties.
        //
        // First we will go through all of the inputs.
        if ((typeof config.inputs !== 'undefined') &&
            (typeof config.inputs.input !== 'undefined')) {
            if ($.isArray(config.inputs.input)) {
                // config.inputs.input is an array

                for (c1 = 0; c1 < config.inputs.input.length; c1++) {
                    addConstFromInput(config.inputs.input[c1]);
                }
            } else if ($.isPlainObject(config.inputs.input)) {
                // config.inputs.input is an object
                addConstFromInput(config.inputs.input);
            }
        }

        // Now we will go through all of the sliders.
        if ((typeof config.sliders !== 'undefined') &&
            (typeof config.sliders.slider !== 'undefined')) {
            if ($.isArray(config.sliders.slider)) {
                // config.sliders.slider is an array

                for (c1 = 0; c1 < config.sliders.slider.length; c1++) {
                    addConstFromSlider(config.sliders.slider[c1]);
                }
            } else if ($.isPlainObject(config.sliders.slider)) {
                // config.sliders.slider is an object
                addConstFromSlider(config.sliders.slider);
            }
        }

        // The constructor will return an object with methods to operate on
        // it's private properties.
        return {
            'getConstValue': getConstValue,
            'setConstValue': setConstValue,
            'bindUpdatePlotEvent': bindUpdatePlotEvent,
            'getAllConstantNames': getAllConstantNames,
            'getAllConstantValues': getAllConstantValues
        };

        function getAllConstantNames() {
            var constName, allConstNames;

            allConstNames = [];

            for (constName in constants) {
                allConstNames.push(constName);
            }

            return allConstNames;
        }

        function getAllConstantValues() {
            var constName, allConstValues;

            allConstValues = [];

            for (constName in constants) {
                allConstValues.push(constants[constName]);
            }

            return allConstValues;
        }

        function bindUpdatePlotEvent(newPlotDiv, callback) {
            plotDiv = newPlotDiv;

            plotDiv.bind('update_plot', callback);
        }

        function getConstValue(constName) {
            if (constants.hasOwnProperty(constName) === false) {
                // If the name of the constant is not tracked by state, return an
                // 'undefined' value.
                return;
            }

            return constants[constName];
        }

        function setConstValue(constName, constValue) {
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
        }

        function addConstFromInput(obj) {
            var constName, constValue;

            // The name of the constant is obj['@var']. The value (initial) of
            // the constant is obj['@initial']. I have taken the word 'initial'
            // into brackets, because multiple inputs and/or sliders can
            // represent the state of a single constant.

            if (typeof obj['@var'] === 'undefined') {
                return;
            }

            constName = obj['@var'];

            if (typeof obj['@initial'] === 'undefined') {
                constValue = 0;
            } else {
                constValue = parseFloat(obj['@initial']);

                if (isNaN(constValue) === true) {
                    constValue = 0;
                }
            }

            constants[constName] = constValue;
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
