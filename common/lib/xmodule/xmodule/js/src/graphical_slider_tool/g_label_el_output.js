// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('GLabelElOutput', [], function () {
    return GLabelElOutput;

    function GLabelElOutput(config, state) {
        if ($.isPlainObject(config.functions["function"])) {
            processFuncObj(config.functions["function"]);
        } else if ($.isArray(config.functions["function"])) {
            (function (c1) {
                while (c1 < config.functions["function"].length) {
                    if ($.isPlainObject(config.functions["function"][c1])) {
                        processFuncObj(config.functions["function"][c1]);
                    }

                    c1 += 1;
                }
            }(0));
        }

        return;

        function processFuncObj(obj) {
            var paramNames, funcString, func, disableAutoReturn;

            // We are only interested in functions that are meant for output to an
            // element.
            if (
                (typeof obj['@output'] !== 'string') ||
                (obj['@output'].toLowerCase() !== 'plot_label')
            ) {
                return;
            }

            if (typeof obj['@el_id'] !== 'string') {
                console.log('ERROR: You specified "output" as "plot_label", but did not spify "el_id".');

                return;
            }

            if (typeof obj['#text'] !== 'string') {
                console.log('ERROR: Function body is not defined.');

                return;
            }

            disableAutoReturn = obj['@disable_auto_return'];

            funcString = obj['#text'];

            if (
                (disableAutoReturn === undefined) ||
                    (
                        (typeof disableAutoReturn === 'string') &&
                        (disableAutoReturn.toLowerCase() !== 'true')
                    )
            ) {
                if (funcString.search(/return/i) === -1) {
                    funcString = 'return ' + funcString;
                }
            } else {
                if (funcString.search(/return/i) === -1) {
                    console.log(
                        'ERROR: You have specified a JavaScript ' +
                        'function without a "return" statemnt. Your ' +
                        'function will return "undefined" by default.'
                    );
                }
            }

            // Make sure that all HTML entities are converted to their proper
            // ASCII text equivalents.
            funcString = $('<div>').html(funcString).text();

            paramNames = state.getAllParameterNames();
            paramNames.push(funcString);

            try {
                func = Function.apply(null, paramNames);
            } catch (err) {
                console.log(
                    'ERROR: The function body "' +
                        funcString +
                        '" was not converted by the Function constructor.'
                );
                console.log('Error message: "' + err.message + '".');

                if (state.showDebugInfo) {
                    $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not create a function from string "' + funcString + '".' + '</div>');
                    $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');
                }

                paramNames.pop();

                return;
            }

            paramNames.pop();

            state.plde.push({
                'elId': obj['@el_id'],
                'func': func
            });
        }

    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
