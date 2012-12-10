// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Inputs', [], function () {
    return Inputs;

    function Inputs(gstId, config, state) {
        var constNamesUsed;

        // There should not be more than one text input per a constant. This
        // just does not make sense. However, nothing really prevents the user
        // from specifying more than one text input for the same constant name.
        // That's why we have to track which constant names already have
        // text inputs for them, and prevent adding further text inputs to
        // these constants.
        //
        // constNamesUsed is an object to which we will add properties having
        // the name of the constant to which we are adding a text input to.
        // When creating a new text input, we must consult with this object, to
        // see if the constant name is not defined as it's property.
        constNamesUsed = {};

        // We will go thorugh all of the inputs, and those that have a valid
        // '@var' property will be added to the page as a HTML text input
        // element.
        if ((typeof config.inputs !== 'undefined') &&
            (typeof config.inputs.input !== 'undefined')) {
            if ($.isArray(config.inputs.input)) {

                // config.inputs.input is an array. For each element, we will
                // add a text input.
                for (c1 = 0; c1 < config.inputs.input.length; c1++) {
                    createInput(config.inputs.input[c1]);
                }
            } else if ($.isPlainObject(config.inputs.input)) {

                // config.inputs.input is an object. Add a text input for it.
                createInput(config.inputs.input);

            }
        }

        function createInput(obj) {
            var constName, constValue, spanEl, inputEl;

            // The name of the constant is obj['@var']. If it is not specified,
            // we will skip creating a text input for this constant.
            if (typeof obj['@var'] !== 'string') {
                return;
            }
            constName = obj['@var'];

            // We will not add a text input for a constant which already has a
            // text input defined for it.
            //
            // We will add the constant name to the 'constNamesUsed' object in
            // the end, when everything went successfully.
            if (constNamesUsed.hasOwnProperty(constName)) {
                return;
            }

            // Multiple sliders and/or inputs can represent the same constant.
            // Therefore we will get the most recent const value from the state
            // object. If it is undefined, we will skip creating a text input
            // for this constant.
            constValue = state.getConstValue(constName);
            if (constValue === undefined) {
                return;
            }

            // With the constant name, and the constant value being defined,
            // lets get the element on the page into which the text input will
            // be inserted.
            spanEl = $('#' + gstId + '_input_' + constName);

            // If a corresponding element for this constant does not exist on
            // the page, we will not be making a text input.
            if (spanEl.length === 0) {
                return;
            }

            // Create the text input element.
            inputEl = $('<input type"text" />');

            // Set the current constant to the text input. It will be visible
            // to the user.
            inputEl.val(constValue);

            // Bind a function to the 'change' event. Whenever the user changes
            // the value of this text input, and presses 'enter' (or clicks
            // somewhere else on the page), this event will be triggered, and
            // our callback will be called.
            inputEl.bind('change', inputOnChange);

            // Lets style the input element nicely. We will use the button()
            // widget for this since there is no native widget for the text
            // input.
            inputEl.button().css({
                'font': 'inherit',
                'color': 'inherit',
                'text-align': 'left',
                'outline': 'none',
                'cursor': 'text',
                'height': '15px',
                'width': '50px'
            });

            // And finally, publish the text input element to the page.
            inputEl.appendTo(spanEl);

            // Don't forget to add the constant to the list of used constants.
            // Next time a slider for this constant will not be created.
            constNamesUsed[constName] = true;

            return;

            // When the user changes the value of this text input, the 'state'
            // will be updated, forcing the plot to be redrawn.
            function inputOnChange(event) {
                state.setConstValue(constName, $(this).val());
            }
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
