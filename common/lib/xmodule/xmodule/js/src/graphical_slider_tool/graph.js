// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Graph', ['logme'], function (logme) {

    return Graph;

    function Graph(gstId, config, state) {
        var plotDiv, dataSeries, functions, xaxis, yaxis, numPoints, xrange,
            asymptotes;

        state.barsConfig = {
            'N': 0,
            'delta': 0,
            'diff': 0,
            'width': 0,
            'width_perc': 0.8,
            'margin': 0.1,
            'total': 0.4,
            'total_half': 0.2
        };

        // We need plot configuration settings. Without them we can't continue.
        if ($.isPlainObject(config.plot) === false) {
            return;
        }

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

        // Sometimes, when height is not explicitly set via CSS (or by some
        // other means), it is 0 pixels by default. When Flot will try to plot
        // a graph in this DIV with 0 height, then it will raise an error. To
        // prevent this, we will set it to be equal to the width.
        if (plotDiv.height() === 0) {
            plotDiv.height(plotDiv.width());
        }

        // Configure some settings for the graph.
        if (setGraphXRange() === false) {
            logme('ERROR: Could not configure the xrange. Will not continue.');

            return;
        }

        if (setGraphAxes() === false) {
            logme('ERROR: Could not process configuration for the axes.');

            return;
        }

        // Get the user defined functions. If there aren't any, don't do
        // anything else.
        createFunctions();

        if (functions.length === 0) {
            logme('ERROR: No functions were specified, or something went wrong.');

            return;
        }

        createMarkingsFunctions();

        // Create the initial graph and plot it for the user to see.
        if (generateData() === true) {
            updatePlot();
        }

        // Bind an event. Whenever some constant changes, the graph will be
        // redrawn
        state.bindUpdatePlotEvent(plotDiv, onUpdatePlot);

        return;

        function createMarkingsFunctions() {
            var c1, paramNames;

            asymptotes = [];
            paramNames = state.getAllParameterNames();

            if ($.isPlainObject(config.plot.asymptote)) {
                processAsymptote(config.plot.asymptote);
            } else if ($.isArray(config.plot.asymptote)) {
                for (c1 = 0; c1 < config.plot.asymptote.length; c1 += 1) {
                    processAsymptote(config.plot.asymptote[c1]);
                }
            }

            return;

            // Read configuration options for asymptotes, and store them as
            // an array of objects. Each object will have 3 properties:
            //
            //    - color: the color of the asymptote line
            //    - type: 'x' (vertical), or 'y' (horizontal)
            //    - func: the function that will generate the value at which
            //            the asymptote will be plotted; i.e. x = func(), or
            //            y = func(); for now only horizontal and vertical
            //            asymptotes are supported
            //
            // Since each asymptote can have a variable function - function
            // that relies on some parameter specified in the config - we will
            // generate each asymptote just before we draw the graph. See:
            //
            //     function updatePlot()
            //     function generateMarkings()
            //
            // Asymptotes are really thin rectangles implemented via the Flot's
            // markings option.
            function processAsymptote(asyObj) {
                var newAsyObj, funcString, func;

                newAsyObj = {};

                if (typeof asyObj['@type'] === 'string') {
                    if (asyObj['@type'].toLowerCase() === 'x') {
                        newAsyObj.type = 'x';
                    } else if (asyObj['@type'].toLowerCase() === 'y') {
                        newAsyObj.type = 'y';
                    } else {
                        logme('ERROR: Attribute "type" for asymptote can be "x" or "y".');

                        return;
                    }
                } else {
                    logme('ERROR: Attribute "type" for asymptote is not specified.');

                    return;
                }

                if (typeof asyObj['#text'] === 'string') {
                    funcString = asyObj['#text'];
                } else {
                    logme('ERROR: Function body for asymptote is not specified.');

                    return;
                }

                newAsyObj.color = '#000';
                if (typeof asyObj['@color'] === 'string') {
                    newAsyObj.color = asyObj['@color'];
                }

                paramNames.push(funcString);

                try {
                    func = Function.apply(null, paramNames);
                } catch (err) {
                    logme('ERROR: Asymptote function body could not be converted to function object.');
                    logme('Error message: "".' + err.message);

                    return;
                }

                paramNames.pop();

                newAsyObj.func = func;
                asymptotes.push(newAsyObj);
            }
        }

        function setGraphAxes() {
            xaxis = {};
            if (typeof config.plot['xticks'] === 'string') {
                if (processTicks(config.plot['xticks'], xaxis, 'xunits') === false) {
                    logme('ERROR: Could not process the ticks for x-axis.');

                    return false;
                }
            } else {
                logme('MESSAGE: "xticks" were not specified. Using defaults.');

                return false;
            }

            yaxis = {};
            if (typeof config.plot['yticks'] === 'string') {
                if (processTicks(config.plot['yticks'], yaxis, 'yunits') === false) {
                    logme('ERROR: Could not process the ticks for y-axis.');

                    return false;
                }
            } else {
                logme('MESSAGE: "yticks" were not specified. Using defaults.');

                return false;
            }

            return true;

            function processTicks(ticksStr, ticksObj, unitsType) {
                var ticksBlobs, tempFloat, tempTicks, c1, c2;

                // The 'ticks' setting is a string containing 3 floating-point
                // numbers.
                ticksBlobs = ticksStr.split(',');

                if (ticksBlobs.length !== 3) {
                    logme('ERROR: Did not get 3 blobs from ticksStr = "' + ticksStr + '".');

                    return false;
                }

                tempFloat = parseFloat(ticksBlobs[0]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.min = tempFloat;
                } else {
                    logme('ERROR: Invalid "min". ticksBlobs[0] = ', ticksBlobs[0]);

                    return false;
                }

                tempFloat = parseFloat(ticksBlobs[1]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.tickSize = tempFloat;
                } else {
                    logme('ERROR: Invalid "tickSize". ticksBlobs[1] = ', ticksBlobs[1]);

                    return false;
                }

                tempFloat = parseFloat(ticksBlobs[2]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.max = tempFloat;
                } else {
                    logme('ERROR: Invalid "max". ticksBlobs[2] = ', ticksBlobs[2]);

                    return false;
                }

                // Is the starting tick to the left of the ending tick (on the
                // x-axis)? If not, set default starting and ending tick.
                if (ticksObj.min >= ticksObj.max) {
                    logme('ERROR: Ticks min >= max.');

                    return false;
                }

                // Make sure the range makes sense - i.e. that there are at
                // least 3 ticks. If not, set a tickSize which will produce
                // 11 ticks. tickSize is the spacing between the ticks.
                if (ticksObj.tickSize > ticksObj.max - ticksObj.min) {
                    logme('ERROR: tickSize > max - min.');

                    return false;
                }

                //  units: change last tick to units
                if (typeof config.plot[unitsType] === 'string') {
                    tempTicks = [];

                    for (c1 = ticksObj.min; c1 <= ticksObj.max; c1 += ticksObj.tickSize) {
                        c2 = roundToPrec(c1, ticksObj.tickSize);
                        tempTicks.push([c2, c2]);
                    }

                    tempTicks.pop();
                    tempTicks.push([
                        roundToPrec(ticksObj.max, ticksObj.tickSize),
                        config.plot[unitsType]
                    ]);

                    ticksObj.tickSize = null;
                    ticksObj.ticks = tempTicks;
                }

                // ticksObj.font = {
                //     'size': '16px'
                // };

                return true;

                function roundToPrec(num, prec) {
                    var c1, tn1, tn2, digitsBefore, digitsAfter;

                    tn1 = Math.abs(num);
                    tn2 = Math.abs(prec);

                    // Find out number of digits BEFORE the decimal point.
                    c1 = 0;
                    tn1 = Math.abs(num);
                    while (tn1 >= 1) {
                        c1 += 1;

                        tn1 /= 10;
                    }
                    digitsBefore = c1;

                    // Find out number of digits AFTER the decimal point.
                    c1 = 0;
                    tn1 = Math.abs(num);
                    while (Math.round(tn1) !== tn1) {
                        c1 += 1;

                        tn1 *= 10;
                    }
                    digitsAfter = c1;

                    // For precision, find out number of digits AFTER the
                    // decimal point.
                    c1 = 0;
                    while (Math.round(tn2) !== tn2) {
                        c1 += 1;

                        tn2 *= 10;
                    }

                    // If precision is more than 1 (no digits after decimal
                    // points).
                    if (c1 === 0) {
                        return num;
                    }

                    // If the precision contains digits after the decimal
                    // point, we apply special rules.
                    else {
                        tn1 = Math.abs(num);

                        // if (digitsAfter > c1) {
                            tn1 = tn1.toFixed(c1);
                        // } else {
                        //     tn1 = tn1.toPrecision(digitsBefore + digitsAfter);
                        // }
                    }

                    if (num < 0) {
                        return -tn1;
                    }

                    return tn1;
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
                logme('Error message: "' + err.message + '"');

                $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not create a function from the string "' + config.plot.xrange.min + '" for xrange.min.' + '</div>');
                $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');

                return false;
            }
            allParamNames.pop();

            allParamNames.push(config.plot.xrange.max);
            try {
                xrange.max = Function.apply(null, allParamNames);
            } catch (err) {
                logme('ERROR: could not create a function from the string "' + config.plot.xrange.max + '" for xrange.max.');
                logme('Error message: "' + err.message + '"');

                $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not create a function from the string "' + config.plot.xrange.max + '" for xrange.max.' + '</div>');
                $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');

                return false;
            }
            allParamNames.pop();

            if (typeof config.plot.num_points !== 'string') {
                // logme('ERROR: config.plot.num_points is not a string.');
                // logme('config.plot.num_points = ', config.plot.num_points);

                tempNum = plotDiv.width() / 5.0;
            }

            tempNum = parseInt(config.plot.num_points, 10);
            if (isFinite(tempNum) === false) {
                // logme('ERROR: Expected config.plot.num_points to be a a valid integer. It is not.');
                // logme('config.plot.num_points = ', config.plot.num_points);

                // return false;

                tempNum = plotDiv.width() / 5.0;
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

            return true;
        }

        function createFunctions() {
            var c1;

            functions = [];

            if (typeof config.functions === 'undefined') {
                logme('ERROR: config.functions is undefined.');

                return;
            }

            if (typeof config.functions.function === 'string') {

                // If just one function string is present.
                addFunction(config.functions.function);

            } else if ($.isPlainObject(config.functions.function) === true) {

                // If a function is present, but it also has properties
                // defined.
                callAddFunction(config.functions.function);

            } else if ($.isArray(config.functions.function)) {

                // If more than one function is defined.
                for (c1 = 0; c1 < config.functions.function.length; c1 += 1) {

                    // For each definition, we must check if it is a simple
                    // string definition, or a complex one with properties.
                    if (typeof config.functions.function[c1] === 'string') {

                        // Simple string.
                        addFunction(config.functions.function[c1]);

                    } else if ($.isPlainObject(config.functions.function[c1])) {

                        // Properties are present.
                        callAddFunction(config.functions.function[c1]);

                    }
                }
            } else {
                logme('ERROR: config.functions.function is of an unsupported type.');

                return;
            }

            return;

            // This function will reduce code duplication. We have to call
            // the function addFunction() several times passing object
            // properties as parameters. Rather than writing them out every
            // time, we will have a single place where it is done.
            function callAddFunction(obj) {
                if (typeof obj['@output'] === 'string') {

                    // If this function is meant to be calculated for an
                    // element then skip it.
                    if (obj['@output'].toLowerCase() === 'element') {
                        return;
                    }

                    // It is an error if "output" is not "element" or "graph".
                    // Though you can ommit the "output" attribute.
                    else if (obj['@output'].toLowerCase() !== 'graph') {
                        logme('ERROR: Function "output" attribute can be either "div" or "graph".');

                        return;
                    }
                }

                // The user did not specify an "output" attribute, or it is
                // "graph".
                addFunction(
                    obj['#text'],
                    obj['@color'],
                    obj['@line'],
                    obj['@dot'],
                    obj['@label'],
                    obj['@point_size'],
                    obj['@fill_area'],
                    obj['@bar']
                );
            }

            function addFunction(funcString, color, line, dot, label,
                                 pointSize, fillArea, bar) {
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

                // Some defaults. If no options are set for the graph, we will
                // make sure that at least a line is drawn for a function.
                newFunctionObject = {
                    'line': true,
                    'dot': false,
                    'bars': false
                };

                // Get all of the parameter names defined by the user in the
                // XML.
                paramNames = state.getAllParameterNames();

                // The 'x' is always one of the function parameters.
                paramNames.push('x');

                // Must make sure that the function body also gets passed to
                // the Function constructor.
                paramNames.push(funcString);

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
                    logme(
                        'ERROR: The function body "' +
                        funcString +
                        '" was not converted by the Function constructor.'
                    );
                    logme('Error message: "' + err.message + '"');

                    $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not create a function from the string "' + funcString + '".' + '</div>');
                    $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');

                    paramNames.pop();
                    paramNames.pop();

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
                    if (line.toLowerCase() === 'true') {
                        newFunctionObject['line'] = true;
                    } else if (line.toLowerCase() === 'false') {
                        newFunctionObject['line'] = false;
                    }
                }

                if (typeof dot === 'string') {
                    if (dot.toLowerCase() === 'true') {
                        newFunctionObject['dot'] = true;
                    } else if (dot.toLowerCase() === 'false') {
                        newFunctionObject['dot'] = false;
                    }
                }

                if (typeof pointSize === 'string') {
                    newFunctionObject['pointSize'] = pointSize;
                }

                if (typeof bar === 'string') {
                    if (bar.toLowerCase() === 'true') {
                        newFunctionObject['bars'] = true;
                    } else if (bar.toLowerCase() === 'false') {
                        newFunctionObject['bars'] = false;
                    }
                }

                if (newFunctionObject['bars'] === true) {
                    newFunctionObject['line'] = false;
                    newFunctionObject['dot'] = false;

                    newFunctionObject.barIndex = state.barsConfig.N;
                    state.barsConfig.N += 1;
                } else if (
                    (newFunctionObject['dot'] === false) &&
                    (newFunctionObject['line'] === false)
                ) {
                    newFunctionObject['line'] = true;
                }

                if (newFunctionObject['line'] === true) {
                    if (typeof fillArea === 'string') {
                        if (fillArea.toLowerCase() === 'true') {
                            newFunctionObject['fillArea'] = true;
                        } else if (fillArea.toLowerCase() === 'false') {
                            newFunctionObject['fillArea'] = false;
                        } else {
                            logme('ERROR: The attribute fill_area should be either "true" or "false".');
                            logme('fill_area = "' + fillArea + '".');

                            return;
                        }
                    }
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
            if (generateData() === true) {
                updatePlot();
            }
        }

        function generateData() {
            var c0, c1, functionObj, seriesObj, dataPoints, paramValues, x, y,
                start, end, step, tempX;

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

                try {
                    start = xrange.min.apply(window, paramValues);
                } catch (err) {
                    logme('ERROR: Could not determine xrange start.');
                    logme('Error message: "' + err.message + '".');

                    $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not determine xrange start from defined function.' + '</div>');
                    $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');

                    return false;
                }
                try {
                    end = xrange.max.apply(window, paramValues);
                } catch (err) {
                    logme('ERROR: Could not determine xrange end.');
                    logme('Error message: "' + err.message + '".');

                    $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not determine xrange end from defined function.' + '</div>');
                    $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');

                    return false;
                }
                step = (end - start) / (numPoints - 1);

                state.barsConfig.delta = (step * state.barsConfig.total) / state.barsConfig.N;
                state.barsConfig.diff = step * state.barsConfig.total_half;

                // Generate the data points.
                for (x = start; x <= end; x += step) {

                    // Push the 'x' variable to the end of the parameter array.
                    paramValues.push(x);

                    // We call the user defined function, passing all of the
                    // available parameter values. Inside this function they
                    // will be accessible by their names.
                    try {
                        y = functionObj.func.apply(window, paramValues);
                    } catch (err) {
                        logme('ERROR: Could not generate data.');
                        logme('Error message: "' + err.message + '".');

                        $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not generate data from defined function.' + '</div>');
                        $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');

                        return false;
                    }

                    if (functionObj.bars === true) {
                        tempX = x - state.barsConfig.diff + (functionObj.barIndex + state.barsConfig.margin) * state.barsConfig.delta;
                    } else {
                        tempX = x;
                    }

                    // Return the paramValues array to how it was before we
                    // added 'x' variable to the end of it.
                    paramValues.pop();

                    // Add the generated point to the data points set.
                    dataPoints.push([tempX, y]);

                    c1 += 1;

                }

                // If the last point did not get included because of rounding
                // of floating-point number addition, then we will include it
                // manually.
                if (c1 != numPoints) {
                    x = end;
                    paramValues.push(x);
                    try {
                        y = functionObj.func.apply(window, paramValues);
                    } catch (err) {
                        logme('ERROR: Could not generate data.');
                        logme('Error message: "' + err.message + '".');

                        $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not generate data from function.' + '</div>');
                        $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');g

                        return false;
                    }
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

                if (functionObj.hasOwnProperty('fillArea') === true) {
                    seriesObj.lines.fill = functionObj.fillArea;
                }

                // Should each data point be represented by a point on the
                // graph?
                seriesObj.points = {
                    'show': functionObj.dot
                };

                seriesObj.bars = {
                    'show': functionObj.bars,
                    'barWidth': state.barsConfig.delta * state.barsConfig.width_perc
                };

                if (functionObj.hasOwnProperty('pointSize')) {
                    seriesObj.points.radius = functionObj.pointSize;
                }

                // Add the newly created series object to the series set which
                // will be plotted by Flot.
                dataSeries.push(seriesObj);
            }

            return true;
        } // End-of: function generateData

        function updatePlot() {
            var paramValues;

            paramValues = state.getAllParameterValues();

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

                    },
                    'grid': {
                        'markings': generateMarkings()
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

            return;

            // Generate markings to represent asymptotes defined by the user.
            // See the following function for more details:
            //
            //     function processAsymptote()
            //
            function generateMarkings() {
                var c1, asymptote, markings, val;

                markings = [];

                for (c1 = 0; c1 < asymptotes.length; c1 += 1) {
                    asymptote = asymptotes[c1];

                    try {
                        val = asymptote.func.apply(window, paramValues);
                    } catch (err) {
                        logme('ERROR: Could not generate value from asymptote function.');
                        logme('Error message: ', err.message);

                        continue;
                    }

                    if (asymptote.type === 'x') {
                        markings.push({
                            'color': asymptote.color,
                            'lineWidth': 1,
                            'xaxis': {
                                'from': val,
                                'to': val
                            }
                        });
                    } else {
                        markings.push({
                            'color': asymptote.color,
                            'lineWidth': 1,
                            'yaxis': {
                                'from': val,
                                'to': val
                            }
                        });

                    }
                }

                return markings;
            }
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
