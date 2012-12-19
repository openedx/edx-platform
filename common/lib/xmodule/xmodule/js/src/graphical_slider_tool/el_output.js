// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('ElOutput', ['logme'], function (logme) {

    return ElOutput;

    function ElOutput(config, state) {

        if ($.isPlainObject(config.plot.function)) {
            processFuncObj(config.plot.function);
        } else if ($.isArray(config.plot.function)) {
            (function (c1) {
                while (c1 < config.plot.function.length) {
                    if ($.isPlainObject(config.plot.function[c1])) {
                        processFuncObj(config.plot.function[c1]);
                    }

                    c1 += 1;
                }
            }(0));
        }

        return;

        function processFuncObj(obj) {
            var outputEl, paramNames, funcString, func;

            // We are only interested in functions that are meant for output to an
            // element.
            if (typeof obj['@output'] !== 'string') {
                return;
            }

            if (obj['@output'].toLowerCase() !== 'element') {
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

            outputEl = $('#' + obj['@el_id']);

            if (outputEl.length !== 1) {
                logme('ERROR: The element with id "' + obj['@el_id'] + '" was not found.');

                return;
            }

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

                paramNames.pop();

                return;
            }

            paramNames.pop();

            outputEl.html(func.apply(window, state.getAllParameterValues()));

            state.addDynamicEl(outputEl, func);
        }

    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
