// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Inputs', ['logme'], function (logme) {
    return Inputs;

    function Inputs(gstId, config, state) {
        logme('Inside "Inputs" module.');
        logme(gstId, config, state);

        // We will go thorugh all of the inputs, and those that have a valid
        // '@var' property will be added to the page as a HTML text input
        // element.
        if ((typeof config.inputs !== 'undefined') &&
            (typeof config.inputs.input !== 'undefined')) {
            if ($.isArray(config.inputs.input)) {
                // config.inputs.input is an array

                for (c1 = 0; c1 < config.inputs.input.length; c1++) {
                    createInput(config.inputs.input[c1]);
                }
            } else if ($.isPlainObject(config.inputs.input)) {
                // config.inputs.input is an object
                createInput(config.inputs.input);
            }
        }

        function createInput(obj) {
            var constName, constValue, spanEl, inputEl;

            if (typeof obj['@var'] !== 'string') {
                return;
            }

            constName = obj['@var'];

            constValue = state.getConstValue(constName);
            if (constValue === undefined) {
                constValue = 0;
            }

            spanEl = $('#' + gstId + '_input_' + constName);

            if (spanEl.length === 0) {
                return;
            }

            inputEl = $('<input type"text" />');

            // inputEl.width(50);
            inputEl.val(constValue);
            inputEl.bind('change', inputOnChange);
            inputEl.button().css({
                'font': 'inherit',
                'color': 'inherit',
                'text-align': 'left',
                'outline': 'none',
                'cursor': 'text',
                'height': '15px',
                'width': '50px'
            });

            inputEl.appendTo(spanEl);

            return;

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
