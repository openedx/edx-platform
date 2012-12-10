// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Graph', [], function () {

    return Graph;

    function Graph(gstId, config, state) {
        var plotDiv, dataSets, functions;

        plotDiv = $('#' + gstId + '_plot');

        if (plotDiv.length === 0) {
            return;
        }

        plotDiv.width(300);
        plotDiv.height(300);

        state.bindUpdatePlotEvent(plotDiv, onUpdatePlot);

        createFunctions();

        generateData();
        updatePlot();

        return;

        function createFunctions() {
            var c1;

            functions = [];

            if (typeof config.plot['function'] === 'undefined') {
                return;
            }

            if (typeof config.plot['function'] === 'string') {
                addFunction(config.plot['function']);
            } else if ($.isPlainObject(config.plot['function']) === true) {

            } else if ($.isArray(config.plot['function'])) {
                for (c1 = 0; c1 < config.plot['function'].length; c1++) {
                    if (typeof config.plot['function'][c1] === 'string') {
                        addFunction(config.plot['function'][c1]);
                    }
                }
            }

            return;

            function addFunction(funcString, color, line, dot, label, style, point_size) {
                var newFunctionObject, func, constNames;

                if (typeof funcString !== 'string') {
                    return;
                }

                newFunctionObject = {};

                constNames = state.getAllConstantNames();

                // The 'x' is always one of the function parameters.
                constNames.push('x');

                // Must make sure that the function body also gets passed to
                // the Function cosntructor.
                constNames.push(funcString);

                func = Function.apply(null, constNames);
                newFunctionObject['func'] = func;

                if (typeof color === 'string') {
                    newFunctionObject['color'] = color;
                }

                if (typeof line === 'boolean') {
                    newFunctionObject['line'] = line;
                }

                if (typeof dot === 'boolean') {
                    newFunctionObject['dot'] = dot;
                }

                if (typeof label === 'string') {
                    newFunctionObject['label'] = label;
                }

                functions.push(newFunctionObject);
            }
        }

        function onUpdatePlot(event) {
            generateData();
            updatePlot();
        }

        function generateData() {
            var c0, c1, datapoints, constValues, x, y;

            constValues = state.getAllConstantValues();

            dataSets = [];

            for (c0 = 0; c0 < functions.length; c0 += 1) {
                datapoints = [];

                for (c1 = 0; c1 < 30; c1 += 0.1) {
                    x = c1;
                    // Push the 'x' variable to the end of the parameter array.
                    constValues.push(x);
                    y = functions[c0].func.apply(window, constValues);
                    constValues.pop();

                    datapoints.push([x, y]);
                }

                dataSets.push(datapoints);
            }
        }

        function updatePlot() {
            $.plot(plotDiv, dataSets);
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
