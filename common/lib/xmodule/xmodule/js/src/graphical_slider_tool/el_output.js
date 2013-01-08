// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('ElOutput', ['logme'], function (logme) {

    return ElOutput;

    function ElOutput(config, state) {

        if ($.isPlainObject(config.functions.function)) {
            processFuncObj(config.functions.function);
        } else if ($.isArray(config.functions.function)) {
            (function (c1) {
                while (c1 < config.functions.function.length) {
                    if ($.isPlainObject(config.functions.function[c1])) {
                        processFuncObj(config.functions.function[c1]);
                    }

                    c1 += 1;
                }
            }(0));
        }

        return;

        function processFuncObj(obj) {
            var paramNames, funcString, func, special, el;

            // We are only interested in functions that are meant for output to an
            // element.
            if (
                (typeof obj['@output'] !== 'string') ||
                (obj['@output'].toLowerCase() !== 'element')
            ) {
                return;
            }

            if (typeof obj['@el_id'] !== 'string') {
                logme('ERROR: You specified "output" as "element", but did not spify "el_id".');

                return;
            }

            if (typeof obj['#text'] !== 'string') {
                logme('ERROR: Function body is not defined.');

                return;
            }

            funcString = obj['#text'];

            // Make sure that all HTML entities are converted to their proper
            // ASCII text equivalents.
            funcString = $('<div>').html(funcString).text();

            paramNames = state.getAllParameterNames();
            paramNames.push(funcString);

            try {
                func = Function.apply(null, paramNames);
            } catch (err) {
                logme(
                    'ERROR: The function body "' +
                        funcString +
                        '" was not converted by the Function constructor.'
                );
                logme('Error message: "' + err.message + '".');

                $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not create a function from string "' + funcString + '".' + '</div>');
                $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');

                paramNames.pop();

                return;
            }

            paramNames.pop();

            special = false;
            if (obj['@el_id'][0] === '_') {
                special = true;
            } else {
                el = $('#' + obj['@el_id']);

                if (el.length !== 1) {
                    logme(
                        'ERROR: DOM element with ID "' + obj['@el_id'] + '" ' +
                        'not found. Dynamic element not created.'
                    );

                    return;
                }

                el.html(func.apply(window, state.getAllParameterValues()));
            }

            state.addDynamicEl(el, func, obj['@el_id'], special);
        }

    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
