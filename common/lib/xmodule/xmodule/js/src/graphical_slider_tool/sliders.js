// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Sliders', ['logme'], function (logme) {
    return Sliders;

    function Sliders(gstId, config, state) {
        logme('We are inside Sliders function.');

        logme('gstId: ' + gstId);
        logme(config);
        logme(state);

        // We will go through all of the sliders. For each one, we will make a
        // jQuery UI slider for it, attach "on change" events, and set it's
        // state - initial value, max, and min parameters.
        if ((typeof config.sliders !== 'undefined') &&
            (typeof config.sliders.slider !== 'undefined')) {
            if ($.isArray(config.sliders.slider)) {
                // config.sliders.slider is an array

                for (c1 = 0; c1 < config.sliders.slider.length; c1++) {
                    createSlider(config.sliders.slider[c1]);
                }
            } else if ($.isPlainObject(config.sliders.slider)) {
                // config.sliders.slider is an object
                createSlider(config.sliders.slider);
            }
        }

        function createSlider(obj) {
            var constName, constValue, rangeBlobs, valueMin, valueMax,
                sliderDiv, sliderWidth;

            // The name of the constant is obj['@var']. Multiple sliders and/or
            // inputs can represent the same constant - therefore we will get
            // the most recent const value from the state object. The range is
            // a string composed of 3 blobs, separated by commas. The first
            // blob is the min value for the slider, the third blob is the max
            // value for the slider.

            if (typeof obj['@var'] === 'undefined') {
                return;
            }

            constName = obj['@var'];

            constValue = state.getConstValue(constName);
            if (constValue === undefined) {
                constValue = 0;
            }

            if (typeof obj['@range'] !== 'string') {
                valueMin = constValue - 10;
                valueMax = constValue + 10;
            } else {
                rangeBlobs = obj['@range'].split(',');

                // We must have gotten exactly 3 blobs (pieces) from the split.
                if (rangeBlobs.length !== 3) {
                    valueMin = constValue - 10;
                    valueMax = constValue + 10;
                } else {
                    // Get the first blob from the split string.
                    valueMin = parseFloat(rangeBlobs[0]);

                    if (isNaN(valueMin) === true) {
                        valueMin = constValue - 10;
                    }

                    // Get the third blob from the split string.
                    valueMax = parseFloat(rangeBlobs[2]);

                    if (isNaN(valueMax) === true) {
                        valueMax = constValue + 10;
                    }

                    // Logically, the min, value, and max should make sense.
                    // I.e. we will make sure that:
                    //
                    //     min <= value <= max
                    //
                    // If this is not the case, we will set some defaults.
                    if ((valueMin > valueMax) ||
                        (valueMin > constValue) ||
                        (valueMax < constValue)) {
                        valueMin = constValue - 10;
                        valueMax = constValue + 10;
                    }
                }
            }

            sliderDiv = $('#' + gstId + '_slider_' + constName);

            // If a corresponding slider  DIV for this constant does not exist,
            // do not do anything.
            if (sliderDiv.length === 0) {
                return;
            }

            // The default slider width.
            sliderWidth = 400;

            logme('width: 0');
            logme(obj['@width']);
            if (typeof obj['@width'] === 'string') {
                logme('width: 1');
                if (isNaN(parseInt(obj['@width'], 10)) === false) {
                    logme('width: 2');
                    sliderWidth = parseInt(obj['@width'], 10);
                }
            }

            // Set the new width to the slider.
            sliderDiv.width(sliderWidth);

            // Create a jQuery UI slider from the current DIV. We will set
            // starting parameters, and will also attach a handler to update
            // the state on the change event.
            sliderDiv.slider({
                'min': valueMin,
                'max': valueMax,
                'value': constValue,

                'change': sliderOnChange
            });

            return;

            function sliderOnChange(event, ui) {
                state.setConstValue(constName, ui.value);
            }
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
