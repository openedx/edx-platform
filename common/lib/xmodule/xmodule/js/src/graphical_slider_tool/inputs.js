// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Inputs', [], function () {
    return Inputs;

    function Inputs(gstId, gstClass, state) {
        var c1, paramName, allParamNames;

        allParamNames = state.getAllParameterNames();

        for (c1 = 0; c1 < allParamNames.length; c1 += 1) {
            $('#' + gstId).find('.' + gstClass + '_input').each(function (index, value) {
                var inputDiv, paramName;

                paramName = allParamNames[c1];
                inputDiv = $(value);

                if (paramName === inputDiv.data('var')) {
                    createInput(inputDiv, paramName);
                }
            });
        }

        return;

        function createInput(inputDiv, paramName) {
            var paramObj;

            paramObj = state.getParamObj(paramName);

            // Check that the retrieval went OK.
            if (paramObj === undefined) {
                console.log('ERROR: Could not get a paramObj for parameter "' + paramName + '".');

                return;
            }

            // Bind a function to the 'change' event. Whenever the user changes
            // the value of this text input, and presses 'enter' (or clicks
            // somewhere else on the page), this event will be triggered, and
            // our callback will be called.
            inputDiv.bind('change', inputOnChange);

            inputDiv.val(paramObj.value);

            // Lets style the input element nicely. We will use the button()
            // widget for this since there is no native widget for the text
            // input.
            inputDiv.button().css({
                'font': 'inherit',
                'color': 'inherit',
                'text-align': 'left',
                'outline': 'none',
                'cursor': 'text',
                'height': '15px'
            });

            // Tell the parameter object from state that we are attaching a
            // text input to it. Next time the parameter will be updated with
            // a new value, tis input will also be updated.
            paramObj.inputDivs.push(inputDiv);

            return;

            // Update the 'state' - i.e. set the value of the parameter this
            // input is attached to to a new value.
            //
            // This will cause the plot to be redrawn each time after the user
            // changes the value in the input. Note that he has to either press
            // 'Enter', or click somewhere else on the page in order for the
            // 'change' event to be tiggered.
            function inputOnChange(event) {
                var inputDiv;

                inputDiv = $(this);
                state.setParameterValue(paramName, inputDiv.val(), inputDiv);
            }
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
