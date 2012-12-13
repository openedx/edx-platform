// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Graph', ['logme'], function (logme) {

    return Graph;

    function Graph(gstId, config, state) {
        var plotDiv, dataSeries, functions, xaxis, yaxis, xrange;

        // We must have a graph container DIV element available in order to
        // proceed.
        plotDiv = $('#' + gstId + '_plot');
        if (plotDiv.length === 0) {
            return;
        }

        // Configure some settings for the graph.
        setGraphDimensions();
        setGraphAxes();
        setGraphXRange();

        // Get the user defined functions. If there aren't any, don't do
        // anything else.
        createFunctions();
        if (functions.length === 0) {
            return;
        }

        // Create the initial graph and plot it for the user to see.
        generateData();
        updatePlot();

        // Bind an event. Whenever some constant changes, the graph will be
        // redrawn
        state.bindUpdatePlotEvent(plotDiv, onUpdatePlot);

        return;

        function setGraphDimensions() {
            var dimObj, width, height, tempInt;

            // If no dimensions are specified by the user, the graph will have
            // predefined dimensions.
            width = 300;
            height = 300;

            // Get the user specified dimensions, if any.
            if ($.isPlainObject(config.plot['dimensions']) === true) {
                dimObj = config.plot['dimensions'];

                tempInt = parseInt(dimObj['@width'], 10);
                if (isNaN(tempInt) === false) {
                    width = tempInt;
                }

                tempInt = parseInt(dimObj['@height'], 10);
                if (isNaN(tempInt) === false) {
                    height = tempInt;
                }
            }

            // Apply the dimensions to the graph container DIV element.
            plotDiv.width(width);
            plotDiv.height(height);
        }

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
            }

            return;

            function processTicks(ticksStr, ticksObj) {
                var ticksBlobs, tempFloat;

                // The 'ticks' setting is a string containing 3 floating-point
                // numbers.
                ticksBlobs = ticksStr.split(',');

                if (ticksBlobs.length !== 3) {
                    return;
                }

                tempFloat = parseFloat(ticksBlobs[0]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.min = tempFloat;
                }

                tempFloat = parseFloat(ticksBlobs[1]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.tickSize = tempFloat;
                }

                tempFloat = parseFloat(ticksBlobs[2]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.max = tempFloat;
                }

                // Is the starting tick to the left of the ending tick (on the
                // x-axis)? If not, set default starting and ending tick.
                if (ticksObj.min >= ticksObj.max) {
                    ticksObj.min = 0;
                    ticksObj.max = 10;
                }

                // Make sure the range makes sense - i.e. that there are at
                // least 3 ticks. If not, set a tickSize which will produce
                // 11 ticks. tickSize is the spacing between the ticks.
                if (ticksObj.tickSize * 2 >= ticksObj.max - ticksObj.min) {
                    ticksObj.tickSize = (ticksObj.max - ticksObj.min) / 10.0;
                }
            }
        }

        function setGraphXRange() {
            var xRangeStr, xRangeBlobs, tempNum;

            xrange = {
                'start': 0,
                'end': 10,
                'step': 0.1
            };
            logme('Default xrange:', xrange);

            // The 'xrange' is a string containing two floating point numbers
            // separated by a comma. The first number is the starting
            // x-coordinate , the second number is the ending x-coordinate
            if (typeof config.plot['xrange'] === 'string') {
                logme('xrange is a string; xrange = "' + config.plot['xrange'] + '".');

                xRangeStr = config.plot['xrange'];
                xRangeBlobs = xRangeStr.split(',');

                if (xRangeBlobs.length === 2) {
                    logme('xrange contains 2 blobs; 1 -> "' + xRangeBlobs[0] + '", 2 -> "' + xRangeBlobs[1] + '".');

                    tempNum = parseFloat(xRangeBlobs[0]);
                    if (isNaN(tempNum) === false) {
                        xrange.start = tempNum;

                        logme('First blob was parsed as a float. xrange.start = "' + xrange.start + '".');
                    } else {
                        logme('ERROR: First blob was parsed as a NaN.');
                    }

                    tempNum = parseFloat(xRangeBlobs[1]);
                    if (isNaN(tempNum) === false) {
                        xrange.end = tempNum;

                        logme('Second blob was parsed as a float. xrange.end = "' + xrange.end + '".');
                    } else {
                        logme('ERROR: Second blob was parsed as a NaN.');
                    }

                    if (xrange.start >= xrange.end) {
                        xrange.start = 0;
                        xrange.end = 10;

                        logme('xrange.start is greater than xrange.end - will set defaults. xrange.start = "' + xrange.start + '". xrange.end = "' + xrange.end + '".');
                    }

                } else {
                    logme('ERROR: xrange does not contain 2 blobs.');
                }
            } else {
                logme('ERROR: xrange is not a string.');
            }

            // The user can specify the number of points. However, internally
            // we will use it to generate a 'step' - i.e. the distance (on
            // x-axis) between two adjacent points.
            if (typeof config.plot['num_points'] === 'string') {
                logme('num_points is a string. num_points = "' + config.plot['num_points'] + '".');

                tempNum = parseInt(config.plot['num_points'], 10);
                if (
                    (isNaN(tempNum) === false) ||
                    (tempNum >= 2) &&
                    (tempNum <= 500)
                ) {
                    logme('num_points was parsed as a number. num_points = "' + tempNum + '".');
                    xrange.step = (xrange.end - xrange.start) / (tempNum - 1);
                    logme('xrange.step = "' + xrange.step + '".');
                } else {
                    logme('ERROR: num_points was not parsed as a number, or num_points < 2, or num_points > 500.');
                }
            } else {
                logme('ERROR: num_points is not a string.');
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
                var newFunctionObject, func, constNames;

                // The main requirement is function string. Without it we can't
                // create a function, and the series cannot be calculated.
                if (typeof funcString !== 'string') {
                    return;
                }

                // Some defaults. If no options are set for the graph, we will
                // make sure that at least a line is drawn for a function.
                newFunctionObject = {
                    'line': true,
                    'dot': false
                };

                // Get all of the constant names defined by the user in the
                // XML.
                constNames = state.getAllConstantNames();

                // The 'x' is always one of the function parameters.
                constNames.push('x');

                // Must make sure that the function body also gets passed to
                // the Function constructor.
                constNames.push(funcString);

                // Create the function from the function string, and all of the
                // available constants + the 'x' variable as it's parameters.
                // For this we will use the built-in Function object
                // constructor.
                //
                // If something goes wrong during this step, most
                // likely the user supplied an invalid JavaScript function body
                // string. In this case we will not proceed.
                try {
                    func = Function.apply(null, constNames);
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
            var c0, functionObj, seriesObj, dataPoints, constValues, x, y;

            constValues = state.getAllConstantValues();

            dataSeries = [];

            for (c0 = 0; c0 < functions.length; c0 += 1) {
                functionObj = functions[c0];

                seriesObj = {};
                dataPoints = [];

                // Generate the data points.
                for (x = xrange.start; x <= xrange.end; x += xrange.step) {

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
