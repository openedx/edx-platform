// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Sliders', [], function () {
    return Sliders;

    function Sliders(gstId, config, state) {
        var constNamesUsed;

        // There should not be more than one slider per a constant. This just
        // does not make sense. However, nothing really prevents the user from
        // specifying more than one slider for the same constant name. That's
        // why we have to track which constant names already have sliders for
        // them, and prevent adding further sliders to these constants.
        //
        // constNamesUsed is an object to which we will add properties having
        // the name of the constant to which we are adding a slider to. When
        // creating a new slider, we must consult with this object, to see if
        // the constant name is not defined as it's property.
        constNamesUsed = {};

        // We will go through all of the sliders. For each one, we will make a
        // jQuery UI slider for it, attach "on change" events, and set it's
        // state - initial value, max, and min parameters.
        if ((typeof config.sliders !== 'undefined') &&
            (typeof config.sliders.slider !== 'undefined')) {
            if ($.isArray(config.sliders.slider)) {

                // config.sliders.slider is an array. For each object in the
                // array, create a slider.
                for (c1 = 0; c1 < config.sliders.slider.length; c1++) {
                    createSlider(config.sliders.slider[c1]);
                }

            } else if ($.isPlainObject(config.sliders.slider)) {

                // config.sliders.slider is an object. Create a slider for it.
                createSlider(config.sliders.slider);

            }
        }

        function createSlider(obj) {
            var constName, constValue, rangeBlobs, valueMin, valueMax, spanEl,
                sliderEl, sliderWidth;

            // The name of the constant is obj['@var']. If it is not specified,
            // we will skip creating a slider for this constant.
            if (typeof obj['@var'] !== 'string') {
                return;
            }
            constName = obj['@var'];

            // We will not add a slider for a constant which already has a
            // slider defined for it.
            //
            // We will add the constant name to the 'constNamesUsed' object in
            // the end, when everything went successfully.
            if (constNamesUsed.hasOwnProperty(constName)) {
                return;
            }

            // Multiple sliders and/or inputs can represent the same constant.
            // Therefore we will get the most recent const value from the state
            // object. If it is undefined, then something terrible has
            // happened! We will skip creating a slider for this constant.
            constValue = state.getConstValue(constName);
            if (constValue === undefined) {
                return;
            }

            // The range is a string composed of 3 blobs, separated by commas.
            // The first blob is the min value for the slider, the third blob
            // is the max value for the slider.
            if (typeof obj['@range'] !== 'string') {

                // If the range is not a string, we will set a default range.
                // No promise as to the quality of the data points that this
                // range will produce.
                valueMin = constValue - 10;
                valueMax = constValue + 10;

            } else {

                // Separate the range string by commas, and store each blob as
                // an element in an array.
                rangeBlobs = obj['@range'].split(',');

                // We must have gotten exactly 3 blobs (pieces) from the split.
                if (rangeBlobs.length !== 3) {

                    // Set some sensible defaults, if the range string was
                    // split into more or less than 3 pieces.
                    setDefaultMinMax();

                } else {

                    // Get the first blob from the split string. It is the min
                    // value.
                    valueMin = parseFloat(rangeBlobs[0]);

                    // Is it a well-formed float number?
                    if (isNaN(valueMin) === true) {

                        // No? Then set a sensible default value.
                        valueMin = constValue - 10;

                    }

                    // Get the third blob from the split string. It is the max.
                    valueMax = parseFloat(rangeBlobs[2]);

                    // Is it a well-formed float number?
                    if (isNaN(valueMax) === true) {

                        // No? Then set a sensible default value.
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

                        // Set some sensible defaults, if min/value/max logic
                        // is broken.
                        setDefaultMinMax();

                    }
                }
            }

            // At this point we have the constant name, the constant value, and
            // the min and max values for this slider. Lets get the element on
            // the page into which the slider will be inserted.
            spanEl = $('#' + gstId + '_slider_' + constName);

            // If a corresponding element for this constant does not exist on
            // the page, we will not be making a slider.
            if (spanEl.length === 0) {
                return;
            }

            // Create the slider DIV.
            sliderEl = $('<div>');

            // We will define the width of the slider to a sensible default.
            sliderWidth = 400;

            // Then we will see if one is provided in the config for this
            // slider. If we find it, and it is a well-formed integer, we will
            // use it, instead of the default width.
            if (typeof obj['@width'] === 'string') {
                if (isNaN(parseInt(obj['@width'], 10)) === false) {
                    sliderWidth = parseInt(obj['@width'], 10);
                }
            }

            // Set the defined width to the slider.
            sliderEl.width(sliderWidth);

            // And make sure that it gets added to the page as an
            // 'inline-block' element. This will allow for the insertion of the
            // slider into a paragraph, without the browser forcing it out of
            // the paragraph onto a new line, separate line.
            sliderEl.css('display', 'inline-block');

            // Create a jQuery UI slider from the slider DIV. We will set
            // starting parameters, and will also attach a handler to update
            // the 'state' on the 'change' event.
            sliderEl.slider({
                'min': valueMin,
                'max': valueMax,
                'value': constValue,
                'step': (valueMax - valueMin) / 50.0,

                // 'change': sliderOnChange,
                'slide': sliderOnChange
            });

            // Append the slider DIV to the element on the page where the user
            // wants to see it.
            sliderEl.appendTo(spanEl);

            // OK! So we made it this far...
            //
            // Adding the constant to the list of used constants. Next time a
            // slider for this constant will not be created.
            constNamesUsed[constName] = true;

            return;

            // Update the 'state' - i.e. set the value of the constant this
            // slider is attached to to a new value.
            //
            // This will cause the plot to be redrawn each time after the user
            // drags the slider handle and releases it.
            function sliderOnChange(event, ui) {
                state.setConstValue(constName, ui.value);
            }

            // The sensible defaults for the slider's range.
            function setDefaultMinMax() {
                valueMin = constValue - 10;
                valueMax = constValue + 10;
            }
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
