// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Sliders', ['logme'], function (logme) {
    return Sliders;

    function Sliders(gstId, gstClass, state) {
        var c1, paramName, allParamNames, sliderDiv;

        allParamNames = state.getAllParameterNames();

        for (c1 = 0; c1 < allParamNames.length; c1 += 1) {
            paramName = allParamNames[c1];

            logme('Looking for slider with ID: ' + gstId + '_slider_' + paramName);
            sliderDiv = $('#' + gstId + '_slider_' + paramName);

            if (sliderDiv.length === 1) {
                logme('Found one slider DIV with such an ID.');
                createSlider(sliderDiv, paramName);
            } else {
                logme('Did not find such a slider.');
            }
        }

        function createSlider(sliderDiv, paramName) {
            var paramObj, sliderWidth;

            paramObj = state.getParamObj(paramName);

            // We will define the width of the slider to a sensible default.
            sliderWidth = 400;

            // See if it was specified by the user.
            if (isFinite(parseInt(sliderDiv.data('el_width'))) === true) {
                sliderWidth = parseInt(sliderDiv.data('el_width'));
            }

            // Set the width of the element.
            sliderDiv.width(sliderWidth);

            sliderDiv.css('display', 'inline-block');

            // Create a jQuery UI slider from the slider DIV. We will set
            // starting parameters, and will also attach a handler to update
            // the 'state' on the 'change' event.
            sliderDiv.slider({
                'min': paramObj.min,
                'max': paramObj.max,
                'value': paramObj.value,
                'step': paramObj.step,

                // 'change': sliderOnChange,
                'slide': sliderOnSlide
            });

            paramObj.sliderDiv = sliderDiv;

            return;

            // Update the 'state' - i.e. set the value of the parameter this
            // slider is attached to to a new value.
            //
            // This will cause the plot to be redrawn each time after the user
            // drags the slider handle and releases it.
            function sliderOnSlide(event, ui) {
                state.setParameterValue(paramName, ui.value, sliderDiv);
            }
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
