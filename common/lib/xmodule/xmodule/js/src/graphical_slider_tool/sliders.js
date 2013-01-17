// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Sliders', ['logme'], function (logme) {
    return Sliders;

    function Sliders(gstId, state) {
        var c1, paramName, allParamNames, sliderDiv;

        allParamNames = state.getAllParameterNames();

        for (c1 = 0; c1 < allParamNames.length; c1 += 1) {
            paramName = allParamNames[c1];

            sliderDiv = $('#' + gstId + '_slider_' + paramName);

            if (sliderDiv.length === 1) {
                createSlider(sliderDiv, paramName);
            } else if (sliderDiv.length > 1) {
                logme('ERROR: Found more than one slider for the parameter "' + paramName + '".');
                logme('sliderDiv.length = ', sliderDiv.length);
            } // else {
            //     logme('MESSAGE: Did not find a slider for the parameter "' + paramName + '".');
            // }
        }

        function createSlider(sliderDiv, paramName) {
            var paramObj;

            paramObj = state.getParamObj(paramName);

            // Check that the retrieval went OK.
            if (paramObj === undefined) {
                logme('ERROR: Could not get a paramObj for parameter "' + paramName + '".');

                return;
            }

            // Create a jQuery UI slider from the slider DIV. We will set
            // starting parameters, and will also attach a handler to update
            // the 'state' on the 'slide' event.
            sliderDiv.slider({
                'min': paramObj.min,
                'max': paramObj.max,
                'value': paramObj.value,
                'step': paramObj.step
            });

            // Tell the parameter object stored in state that we have a slider
            // that is attached to it. Next time when the parameter changes, it
            // will also update the value of this slider.
            paramObj.sliderDiv = sliderDiv;

            // Atach callbacks to update the slider's parameter.
            paramObj.sliderDiv.on('slide', sliderOnSlide);
            paramObj.sliderDiv.on('slidechange', sliderOnChange);

            return;

            // Update the 'state' - i.e. set the value of the parameter this
            // slider is attached to to a new value.
            //
            // This will cause the plot to be redrawn each time after the user
            // drags the slider handle and releases it.
            function sliderOnSlide(event, ui) {
                // Last parameter passed to setParameterValue() will be 'true'
                // so that the function knows we are a slider, and it can
                // change the our value back in the case when the new value is
                // invalid for some reason.
                if (state.setParameterValue(paramName, ui.value, sliderDiv, true, 'slide') === undefined) {
                    logme('ERROR: Could not update the parameter named "' + paramName + '" with the value "' + ui.value + '".');
                }
            }

            function sliderOnChange(event, ui) {
                if (state.setParameterValue(paramName, ui.value, sliderDiv, true, 'change') === undefined) {
                    logme('ERROR: Could not update the parameter named "' + paramName + '" with the value "' + ui.value + '".');
                }
            }
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
