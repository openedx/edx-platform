// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Graph', ['logme'], function (logme) {

    return Graph;

    function Graph(gstId, config, state) {
        var plotDiv, dataSeries, functions, xaxis, yaxis, numPoints, xrange;

        // We must have a graph container DIV element available in order to
        // proceed.
        plotDiv = $('#' + gstId + '_plot');
        if (plotDiv.length === 0) {
            logme('ERROR: Could not find the plot DIV with ID "' + gstId + '_plot".');

            return;
        }

        if (plotDiv.width() === 0) {
            plotDiv.width(300);
        }

        if (plotDiv.height() === 0) {
            plotDiv.height(plotDiv.width());
        }

        // Configure some settings for the graph.
        if (setGraphXRange() === false) {
            logme('ERROR: could not configure the xrange. Will not continue.');

            return;
        }

        setGraphAxes();

        // Get the user defined functions. If there aren't any, don't do
        // anything else.
        createFunctions();
        if (functions.length === 0) {
            logme('ERROR: No functions were specified, or something went wrong.');

            return;
        }

        // Create the initial graph and plot it for the user to see.
        generateData();
        updatePlot();

        // Bind an event. Whenever some constant changes, the graph will be
        // redrawn
        state.bindUpdatePlotEvent(plotDiv, onUpdatePlot);

        return;

        function setGraphAxes() {
            // Define the xaxis Flot configuration, and then see if the user
            // supplied custom values.
            xaxis = {
                'min': 0,
                'tickSize': 1,
                'max': 10
            };
            if (typeof config.plot['xticks'] === 'string') {
                processTicks(config.plot['xticks'], xaxis);
            } else {
                logme('MESSAGE: "xticks" were not specified. Using defaults.');
            }

            // Define the yaxis Flot configuration, and then see if the user
            // supplied custom values.
            yaxis = {
                'min': 0,
                'tickSize': 1,
                'max': 10
            };
            if (typeof config.plot['yticks'] === 'string') {
                processTicks(config.plot['yticks'], yaxis);
            } else {
                logme('MESSAGE: "yticks" were not specified. Using defaults.');
            }

            return;

            function processTicks(ticksStr, ticksObj) {
                var ticksBlobs, tempFloat;

                // The 'ticks' setting is a string containing 3 floating-point
                // numbers.
                ticksBlobs = ticksStr.split(',');

                if (ticksBlobs.length !== 3) {
                    logme('ERROR: Did not get 3 blobs from ticksStr = "' + ticksStr + '".');

                    return;
                }

                tempFloat = parseFloat(ticksBlobs[0]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.min = tempFloat;
                } else {
                    logme('ERROR: Invalid "min". ticksBlobs[0] = ', ticksBlobs[0]);
                }

                tempFloat = parseFloat(ticksBlobs[1]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.tickSize = tempFloat;
                } else {
                    logme('ERROR: Invalid "tickSize". ticksBlobs[1] = ', ticksBlobs[1]);
                }

                tempFloat = parseFloat(ticksBlobs[2]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.max = tempFloat;
                } else {
                    logme('ERROR: Invalid "max". ticksBlobs[2] = ', ticksBlobs[2]);
                }

                // Is the starting tick to the left of the ending tick (on the
                // x-axis)? If not, set default starting and ending tick.
                if (ticksObj.min >= ticksObj.max) {
                    logme('ERROR: min >= max. Setting defaults.');

                    ticksObj.min = 0;
                    ticksObj.max = 10;
                }

                // Make sure the range makes sense - i.e. that there are at
                // least 3 ticks. If not, set a tickSize which will produce
                // 11 ticks. tickSize is the spacing between the ticks.
                if (ticksObj.tickSize * 2 >= ticksObj.max - ticksObj.min) {
                    logme('ERROR: tickSize * 2 >= max - min. Setting defaults.');

                    ticksObj.tickSize = (ticksObj.max - ticksObj.min) / 10.0;
                }
            }
        }

        function setGraphXRange() {
            var xRangeStr, xRangeBlobs, tempNum, allParamNames;

            xrange = {};

            if ($.isPlainObject(config.plot.xrange) === false) {
                logme('ERROR: Expected config.plot.xrange to be an object. It is not.');
                logme('config.plot.xrange = ', config.plot.xrange);

                return false;
            }

            if (typeof config.plot.xrange.min !== 'string') {
                logme('ERROR: Expected config.plot.xrange.min to be a string. It is not.');
                logme('config.plot.xrange.min = ', config.plot.xrange.min);

                return false;
            }

            if (typeof config.plot.xrange.max !== 'string') {
                logme('ERROR: Expected config.plot.xrange.max to be a string. It is not.');
                logme('config.plot.xrange.max = ', config.plot.xrange.max);

                return false;
            }

            allParamNames = state.getAllParameterNames();

            allParamNames.push(config.plot.xrange.min);
            try {
                xrange.min = Function.apply(null, allParamNames);
            } catch (err) {
                logme('ERROR: could not create a function from the string "' + config.plot.xrange.min + '" for xrange.min.');

                return false;
            }
            allParamNames.pop();

            allParamNames.push(config.plot.xrange.max);
            try {
                xrange.max = Function.apply(null, allParamNames);
            } catch (err) {
                logme('ERROR: could not create a function from the string "' + config.plot.xrange.min + '" for xrange.min.');

                return false;
            }
            allParamNames.pop();

            logme('xrange = ', xrange);

            // The user can specify the number of points. However, internally
            // we will use it to generate a 'step' - i.e. the distance (on
            // x-axis) between two adjacent points.
            if (typeof config.plot.num_points === 'string') {
                tempNum = parseInt(config.plot.num_points, 10);
                if (isNaN(tempNum) === true) {
                    logme('ERROR: Could not parse the number of points.');
                    logme('config.plot.num_points = ', config.plot.num_points);

                    return false;
                }

                if (
                    (tempNum < 2) &&
                    (tempNum > 1000)
                ) {
                    logme('ERROR: Number of points is outside the allowed range [2, 1000]');
                    logme('config.plot.num_points = ' + tempNum);

                    return false;
                }

                numPoints = tempNum;
            } else {
                logme('MESSAGE: config.plot.num_points is not a string.');
                logme('Will set number of points to {width of graph} / 10.');

                numPoints = plotDiv.width() / 10.0;

                logme('numPoints = ' + numPoints);
            }

            return true;
        }

        function createFunctions() {
            var c1;

            functions = [];

            if (typeof config.plot['function'] === 'undefined') {
                logme('ERROR: config.plot["function"] is undefined.');

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
            } else {
                logme('ERROR: config.plot["function"] is of an unsupported type.');

                return;
            }

            return;

            // This function will reduce code duplication. We have to call
            // the function addFunction() several times passing object
            // properties as parameters. Rather than writing them out every
            // time, we will have a single place where it is done.
            function callAddFunction(obj) {
                addFunction(
                    obj['#text'],
                    obj['@color'],
                    obj['@line'],
                    obj['@dot'],
                    obj['@label']
                );
            }

            function addFunction(funcString, color, line, dot, label) {
                var newFunctionObject, func, paramNames;

                // The main requirement is function string. Without it we can't
                // create a function, and the series cannot be calculated.
                if (typeof funcString !== 'string') {
                    return;
                }

                // Make sure that any HTML entities that were escaped will be
                // unescaped. This is done because if a string with escaped
                // HTML entities is passed to the Function() constructor, it
                // will break.
                funcString = $('<div>').html(funcString).text();

                logme('funcString = ' + funcString);

                // Some defaults. If no options are set for the graph, we will
                // make sure that at least a line is drawn for a function.
                newFunctionObject = {
                    'line': true,
                    'dot': false
                };

                // Get all of the parameter names defined by the user in the
                // XML.
                paramNames = state.getAllParameterNames();

                logme('allParamNames = ', paramNames);

                // The 'x' is always one of the function parameters.
                paramNames.push('x');

                // Must make sure that the function body also gets passed to
                // the Function constructor.
                paramNames.push(funcString);

                console.log('paramNames = ', paramNames);

                // Create the function from the function string, and all of the
                // available parameters AND the 'x' variable as it's parameters.
                // For this we will use the built-in Function object
                // constructor.
                //
                // If something goes wrong during this step, most
                // likely the user supplied an invalid JavaScript function body
                // string. In this case we will not proceed.
                try {
                    func = Function.apply(null, paramNames);
                } catch (err) {
                    // Let's tell the user. He will see a nice red error
                    // message instead of a graph.
                    plotDiv.html(
                        '<span style="color: red;">' +
                            'Error while parsing JavaScript function body string!' +
                        '</span>'
                    );

                    return;
                }

                // Return the array back to original state. Remember that it is
                // a pointer to original array which is stored in state object.
                paramNames.pop();
                paramNames.pop();

                newFunctionObject['func'] = func;

                if (typeof color === 'string') {
                    newFunctionObject['color'] = color;
                }

                if (typeof line === 'string') {
                    if (line === 'true') {
                        newFunctionObject['line'] = true;
                    } else if (line === 'false') {
                        newFunctionObject['line'] = false;
                    }
                }

                if (typeof dot === 'string') {
                    if (dot === 'true') {
                        newFunctionObject['dot'] = true;
                    } else if (dot === 'false') {
                        newFunctionObject['dot'] = false;
                    }
                }

                // If the preference is conflicting (we must have either line
                // or dot, none is not an option), we will show line.
                if (
                    (newFunctionObject['dot'] === false) &&
                    (newFunctionObject['line'] === false)
                ) {
                    newFunctionObject['line'] = true;
                }

                if (typeof label === 'string') {
                    newFunctionObject['label'] = label;
                }

                functions.push(newFunctionObject);
            }
        }

        // The callback that will be called whenever a constant changes (gets
        // updated via a slider or a text input).
        function onUpdatePlot(event) {
            generateData();
            updatePlot();
        }

        function generateData() {
            var c0, c1, functionObj, seriesObj, dataPoints, paramValues, x, y,
                start, end, step;

            paramValues = state.getAllParameterValues();

            dataSeries = [];

            for (c0 = 0; c0 < functions.length; c0 += 1) {
                functionObj = functions[c0];

                seriesObj = {};
                dataPoints = [];

                // For counting number of points added. In the end we will
                // compare this number to 'numPoints' specified in the config
                // JSON.
                c1 = 0;

                start = xrange.min.apply(window, paramValues);
                end = xrange.max.apply(window, paramValues);
                step = (end - start) / (numPoints - 1);

                logme('start = ' + start + ', end = ' + end + ', step = ' + step);

                // Generate the data points.
                for (x = start; x <= end; x += step) {

                    // Push the 'x' variable to the end of the parameter array.
                    paramValues.push(x);

                    // We call the user defined function, passing all of the
                    // available parameter values. Inside this function they
                    // will be accessible by their names.
                    y = functionObj.func.apply(window, paramValues);

                    // Return the paramValues array to how it was before we
                    // added 'x' variable to the end of it.
                    paramValues.pop();

                    // Add the generated point to the data points set.
                    dataPoints.push([x, y]);

                    c1 += 1;

                }

                // If the last point did not get included because of rounding
                // of floating-point number addition, then we will include it
                // manually.
                if (c1 != numPoints) {
                    x = end;
                    paramValues.push(x);
                    y = functionObj.func.apply(window, paramValues);
                    paramValues.pop();
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

                // Should the data points be connected by a line?
                seriesObj.lines = {
                    'show': functionObj.line
                };

                // Should each data point be represented by a point on the
                // graph?
                seriesObj.points = {
                    'show': functionObj.dot
                };

                // Add the newly created series object to the series set which
                // will be plotted by Flot.
                dataSeries.push(seriesObj);
            }
        }

        function updatePlot() {
            // Tell Flot to draw the graph to our specification.
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

            // The first time that the graph gets added to the page, the legend
            // is created from scratch. When it appears, MathJax works some
            // magic, and all of the specially marked TeX gets rendered nicely.
            // The next time when we update the graph, no such thing happens.
            // We must ask MathJax to typeset the legend again (well, we will
            // ask it to look at our entire graph DIV), the next time it's
            // worker queue is available.
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
