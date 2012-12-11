// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Graph', ['logme'], function (logme) {

    return Graph;

    function Graph(gstId, config, state) {
        var plotDiv, dataSeries, functions, xaxis, yaxis;

        logme('config:', config);

        plotDiv = $('#' + gstId + '_plot');

        if (plotDiv.length === 0) {
            return;
        }

        setGraphDimensions();
        setGraphAxes();

        state.bindUpdatePlotEvent(plotDiv, onUpdatePlot);

        createFunctions();

        generateData();
        updatePlot();

        return;

        function setGraphDimensions() {
            var dimObj, width, height;

            // If no dimensions are specified by the user, the graph have
            // predefined dimensions.
            width = 300;
            height = 300;

            // Get the user specified dimensions, if any.
            if ($.isPlainObject(config.plot['dimensions']) === true) {
                dimObj = config.plot['dimensions'];

                if (dimObj.hasOwnProperty('@width') === true) {
                    if (isNaN(parseInt(dimObj['@width'], 10)) === false) {
                        width = parseInt(dimObj['@width'], 10);
                    }
                }

                if (dimObj.hasOwnProperty('@height') === true) {
                    if (isNaN(parseInt(dimObj['@height'], 10)) === false) {
                        height = parseInt(dimObj['@height'], 10);
                    }
                }
            }

            plotDiv.width(width);
            plotDiv.height(height);
        }

        function setGraphAxes() {
            xaxis = {
                'min': 0,
                'tickSize': 3,
                'max': 30
            };

            if (typeof config.plot['xticks'] === 'string') {
                processTicks(config.plot['xticks'], xaxis);
            }

            yaxis = {
                'min': -5,
                'tickSize': 1,
                'max': 5
            };

            if (typeof config.plot['yticks'] === 'string') {
                processTicks(config.plot['yticks'], yaxis);
            }

            return;

            function processTicks(ticksStr, ticksObj) {
                var ticksBlobs, min, tickSize, max;

                logme('Processing ticks. Ticks string is: [' + ticksStr + ']');
                logme('Original ticks object:', ticksObj);

                ticksBlobs = ticksStr.split(',');

                if (ticksBlobs.length !== 3) {
                    return;
                }

                min = parseFloat(ticksBlobs[0]);
                if (isNaN(min) === false) {
                    ticksObj.min = min;
                }

                tickSize = parseFloat(ticksBlobs[1]);
                if (isNaN(tickSize) === false) {
                    ticksObj.tickSize = tickSize;
                }

                max = parseFloat(ticksBlobs[2]);
                if (isNaN(max) === false) {
                    ticksObj.max = max;
                }

                if (ticksObj.min >= ticksObj.max) {
                    ticksObj.min = 0;
                    ticksObj.max = 10;
                }

                if (ticksObj.tickSize * 2 >= ticksObj.max - ticksObj.min) {
                    ticksObj.tickSize = (ticksObj.max - ticksObj.min) / 10.0;
                }

                logme('Modified ticks object:', ticksObj);
            }
        }

        function createFunctions() {
            var c1;

            functions = [];

            if (typeof config.plot['function'] === 'undefined') {
                return;
            }

            if (typeof config.plot['function'] === 'string') {

                // If just one function string is present.
                addFunction(config.plot['function']);

            } else if ($.isPlainObject(config.plot['function']) === true) {

                // If a function is present, but it also has properties
                // defined.
                callAddFunction(config.plot['function']);

            } else if ($.isArray(config.plot['function'])) {

                // If more than one function is defined.
                for (c1 = 0; c1 < config.plot['function'].length; c1++) {

                    // For each definition, we must check if it is a simple
                    // string definition, or a complex one with properties.
                    if (typeof config.plot['function'][c1] === 'string') {

                        // Simple string.
                        addFunction(config.plot['function'][c1]);

                    } else if ($.isPlainObject(config.plot['function'][c1])) {

                        // Properties are present.
                        callAddFunction(config.plot['function'][c1]);

                    }
                }
            }

            return;

            // This function will reduce code duplications. We have to call
            // the function addFunction() several times passing object
            // properties. A parameters. Rather than writing them out every
            // time, we will have a single point of
            function callAddFunction(obj) {
                addFunction(
                    obj['#text'],
                    obj['@color'],
                    obj['@line'],
                    obj['@dot'],
                    obj['@label'],
                    obj['@style'],
                    obj['@point_size']
                );
            }

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

                if ((typeof line === 'boolean') || (typeof line === 'string')) {
                    if ((line === 'true') || (line === true)) {
                        newFunctionObject['line'] = true;
                    } else {
                        newFunctionObject['line'] = false;
                    }
                }

                if ((typeof dot === 'boolean') || (typeof dot === 'string')) {
                    if ((dot === 'true') || (dot === true)) {
                        newFunctionObject['dot'] = true;
                    } else {
                        newFunctionObject['dot'] = false;
                    }
                }

                // By default, if no preference was set, or if the preference
                // is conflicting (we must have either line or dot, none is
                // not an option), we will show line.
                if ((newFunctionObject['dot'] === false) && (newFunctionObject['line'] === false)) {
                    newFunctionObject['line'] = true;
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
            var c0, c1, functionObj, seriesObj, dataPoints, constValues, x, y;

            constValues = state.getAllConstantValues();

            dataSeries = [];

            for (c0 = 0; c0 < functions.length; c0 += 1) {
                functionObj = functions[c0];

                seriesObj = {};
                dataPoints = [];

                for (c1 = 0; c1 < 30; c1 += 1) {
                    x = c1;

                    // Push the 'x' variable to the end of the parameter array.
                    constValues.push(x);

                    // We call the user defined function, passing all of the
                    // available constant values. inside this function they
                    // will be accessible by their names.
                    y = functionObj.func.apply(window, constValues);

                    // Return the constValues array to how it was before we
                    // added 'x' variable to the end of it.
                    constValues.pop();

                    // Add the generated point to the data points set.
                    dataPoints.push([x, y]);

                }

                // Put the entire data points set into the series object.
                seriesObj.data = dataPoints;

                // See if user defined a specific color for this function.
                if (functionObj.hasOwnProperty('color') === true) {
                    seriesObj.color = functionObj.color;
                }

                // See if a user defined a label for this function.
                if (functionObj.hasOwnProperty('label') === true) {
                    seriesObj.label = functionObj.label;
                }

                seriesObj.lines = {
                    'show': functionObj.line
                };

                seriesObj.points = {
                    'show': functionObj.dot
                };

                dataSeries.push(seriesObj);
            }
        }

        function updatePlot() {
            $.plot(
                plotDiv,
                dataSeries,
                {
                    'xaxis': xaxis,
                    'yaxis': yaxis,
                    'legend': {

                        // To show the legend or not. Note, even if 'show' is
                        // 'true', the legend will only show if labels are
                        // provided for at least one of the series that are
                        // going to be plotted.
                        'show': true,

                        // A floating point number in the range [0, 1]. The
                        // smaller the number, the more transparent will the
                        // legend background become.
                        'backgroundOpacity': 0

                    }
                }
            );

            MathJax.Hub.Queue([
                'Typeset',
                MathJax.Hub,
                plotDiv.attr('id')
            ]);
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
