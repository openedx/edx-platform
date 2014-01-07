// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Graph', [], function () {

    return Graph;

    function Graph(gstId, config, state) {
        var plotDiv, dataSeries, functions, xaxis, yaxis, numPoints, xrange,
            asymptotes, movingLabels, xTicksNames, yTicksNames, graphBarWidth, graphBarAlign;

        // We need plot configuration settings. Without them we can't continue.
        if ($.isPlainObject(config.plot) === false) {
            return;
        }

        // We must have a graph container DIV element available in order to
        // proceed.
        plotDiv = $('#' + gstId + '_plot');
        if (plotDiv.length === 0) {
            console.log('ERROR: Could not find the plot DIV with ID "' + gstId + '_plot".');

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

        plotDiv.css('position', 'relative');

        // Configure some settings for the graph.
        if (setGraphXRange() === false) {
            console.log('ERROR: Could not configure the xrange. Will not continue.');

            return;
        }

        if (setGraphAxes() === false) {
            console.log('ERROR: Could not process configuration for the axes.');

            return;
        }

        graphBarWidth = 1;
        graphBarAlign = null;

        getBarWidth();
        getBarAlign();

        // Get the user defined functions. If there aren't any, don't do
        // anything else.
        createFunctions();

        if (functions.length === 0) {
            console.log('ERROR: No functions were specified, or something went wrong.');

            return;
        }

        if (createMarkingsFunctions() === false) {
            return;
        }
        if (createMovingLabelFunctions() === false) {
            return;
        }

        // Create the initial graph and plot it for the user to see.
        if (generateData() === true) {
            updatePlot();
        }

        // Bind an event. Whenever some constant changes, the graph will be
        // redrawn
        state.bindUpdatePlotEvent(plotDiv, onUpdatePlot);

        return;

        function getBarWidth() {
            if (config.plot.hasOwnProperty('bar_width') === false) {
                return;
            }

            if (typeof config.plot.bar_width !== 'string') {
                console.log('ERROR: The parameter config.plot.bar_width must be a string.');

                return;
            }

            if (isFinite(graphBarWidth = parseFloat(config.plot.bar_width)) === false) {
                console.log('ERROR: The parameter config.plot.bar_width is not a valid floating number.');
                graphBarWidth = 1;

                return;
            }

            return;
        }

        function getBarAlign() {
            if (config.plot.hasOwnProperty('bar_align') === false) {
                return;
            }

            if (typeof config.plot.bar_align !== 'string') {
                console.log('ERROR: The parameter config.plot.bar_align must be a string.');

                return;
            }

            if (
                (config.plot.bar_align.toLowerCase() !== 'left') &&
                (config.plot.bar_align.toLowerCase() !== 'center')
            ) {
                console.log('ERROR: Property config.plot.bar_align can be one of "left", or "center".');

                return;
            }

            graphBarAlign = config.plot.bar_align.toLowerCase();

            return;
        }

        function createMovingLabelFunctions() {
            var c1, returnStatus;

            returnStatus = true;
            movingLabels = [];

            if (config.plot.hasOwnProperty('moving_label') !== true) {
                returnStatus = true;
            } else if ($.isPlainObject(config.plot.moving_label) === true) {
                if (processMovingLabel(config.plot.moving_label) === false) {
                    returnStatus = false;
                }
            } else if ($.isArray(config.plot.moving_label) === true) {
                for (c1 = 0; c1 < config.plot.moving_label.length; c1++) {
                    if (processMovingLabel(config.plot.moving_label[c1]) === false) {
                        returnStatus = false;
                    }
                }
            }

            return returnStatus;
        }

        function processMovingLabel(obj) {
            var labelText, funcString, disableAutoReturn, paramNames, func,
                fontWeight, fontColor;

            if (obj.hasOwnProperty('@text') === false) {
                console.log('ERROR: You did not define a "text" attribute for the moving_label.');

                return false;
            }
            if (typeof obj['@text'] !== 'string') {
                console.log('ERROR: "text" attribute is not a string.');

                return false;
            }
            labelText = obj['@text'];

            if (obj.hasOwnProperty('#text') === false) {
                console.log('ERROR: moving_label is missing function declaration.');

                return false;
            }
            if (typeof obj['#text'] !== 'string') {
                console.log('ERROR: Function declaration is not a string.');

                return false;
            }
            funcString = obj['#text'];

            fontColor = 'black';
            if (
                (obj.hasOwnProperty('@color') === true) &&
                (typeof obj['@color'] === 'string')
            ) {
                fontColor = obj['@color'];
            }

            fontWeight = 'normal';
            if (
                (obj.hasOwnProperty('@weight') === true) &&
                (typeof obj['@weight'] === 'string')
            ) {
                if (
                    (obj['@weight'].toLowerCase() === 'normal') ||
                    (obj['@weight'].toLowerCase() === 'bold')
                ) {
                    fontWeight = obj['@weight'];
                } else {
                    console.log('ERROR: Moving label can have a weight property of "normal" or "bold".');
                }
            }

            disableAutoReturn = obj['@disable_auto_return'];

            funcString = $('<div>').html(funcString).text();

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
                console.log('Error message: "' + err.message + '"');

                if (state.showDebugInfo) {
                    $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not create a function from the string "' + funcString + '".' + '</div>');
                    $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');
                }

                paramNames.pop();

                return false;
            }

            paramNames.pop();

            movingLabels.push({
                'labelText': labelText,
                'func': func,
                'el': null,
                'fontColor': fontColor,
                'fontWeight': fontWeight
            });

            return true;
        }

        function createMarkingsFunctions() {
            var c1, paramNames, returnStatus;

            returnStatus = true;

            asymptotes = [];
            paramNames = state.getAllParameterNames();

            if ($.isPlainObject(config.plot.asymptote)) {
                if (processAsymptote(config.plot.asymptote) === false) {
                    returnStatus = false;
                }
            } else if ($.isArray(config.plot.asymptote)) {
                for (c1 = 0; c1 < config.plot.asymptote.length; c1 += 1) {
                    if (processAsymptote(config.plot.asymptote[c1]) === false) {
                        returnStatus = false;
                    }
                }
            }

            return returnStatus;

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
                        console.log('ERROR: Attribute "type" for asymptote can be "x" or "y".');

                        return false;
                    }
                } else {
                    console.log('ERROR: Attribute "type" for asymptote is not specified.');

                    return false;
                }

                if (typeof asyObj['#text'] === 'string') {
                    funcString = asyObj['#text'];
                } else {
                    console.log('ERROR: Function body for asymptote is not specified.');

                    return false;
                }

                newAsyObj.color = '#000';
                if (typeof asyObj['@color'] === 'string') {
                    newAsyObj.color = asyObj['@color'];
                }

                newAsyObj.label = false;
                if (
                    (asyObj.hasOwnProperty('@label') === true) &&
                    (typeof asyObj['@label'] === 'string')
                ) {
                    newAsyObj.label = asyObj['@label'];
                }

                funcString = $('<div>').html(funcString).text();

                disableAutoReturn = asyObj['@disable_auto_return'];
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

                paramNames.push(funcString);

                try {
                    func = Function.apply(null, paramNames);
                } catch (err) {
                    console.log('ERROR: Asymptote function body could not be converted to function object.');
                    console.log('Error message: "".' + err.message);

                    return false;
                }

                paramNames.pop();

                newAsyObj.func = func;
                asymptotes.push(newAsyObj);

                return true;
            }
        }

        function setGraphAxes() {
            xaxis = {
                'tickFormatter': null
            };

            if (typeof config.plot['xticks'] === 'string') {
                if (processTicks(config.plot['xticks'], xaxis, 'xunits') === false) {
                    console.log('ERROR: Could not process the ticks for x-axis.');

                    return false;
                }
            } else {
                // console.log('MESSAGE: "xticks" were not specified. Using defaults.');

                return false;
            }

            yaxis = {
                'tickFormatter': null
            };
            if (typeof config.plot['yticks'] === 'string') {
                if (processTicks(config.plot['yticks'], yaxis, 'yunits') === false) {
                    console.log('ERROR: Could not process the ticks for y-axis.');

                    return false;
                }
            } else {
                // console.log('MESSAGE: "yticks" were not specified. Using defaults.');

                return false;
            }

            xTicksNames = null;
            yTicksNames = null;

            if (checkForTicksNames('x') === false) {
                return false;
            }

            if (checkForTicksNames('y') === false) {
                return false;
            }

            return true;

            //
            // function checkForTicksNames(axisName)
            //
            // The parameter "axisName" can be either "x" or "y" (string). Depending on it, the function
            // will set "xTicksNames" or "yTicksNames" private variable.
            //
            // This function does not return anything. It sets the private variable "xTicksNames" ("yTicksNames")
            // to the object converted by JSON.parse from the XML parameter "plot.xticks_names" ("plot.yticks_names").
            // If the "plot.xticks_names" ("plot.yticks_names") is missing or it is not a valid JSON string, then
            // "xTicksNames" ("yTicksNames") will be set to "null".
            //
            // Depending on the "xTicksNames" ("yTicksNames") being "null" or an object, the plot will either draw
            // number ticks, or use the names specified by the opbject.
            //
            function checkForTicksNames(axisName) {
                var tmpObj;

                if ((axisName !== 'x') && (axisName !== 'y')) {
                    // This is not an error. This funcion should simply stop executing.

                    return true;
                }

                if (
                    (config.plot.hasOwnProperty(axisName + 'ticks_names') === true) ||
                    (typeof config.plot[axisName + 'ticks_names'] === 'string')
                ) {
                    try {
                        tmpObj = JSON.parse(config.plot[axisName + 'ticks_names']);
                    } catch (err) {
                        console.log(
                            'ERROR: plot.' + axisName + 'ticks_names is not a valid JSON string.',
                            'Error message: "' + err.message + '".'
                        );

                        return false;
                    }

                    if (axisName === 'x') {
                        xTicksNames = tmpObj;
                        xaxis.tickFormatter = xAxisTickFormatter;
                    }
                    // At this point, we are certain that axisName = 'y'.
                    else {
                        yTicksNames = tmpObj;
                        yaxis.tickFormatter = yAxisTickFormatter;
                    }
                }
            }

            function processTicks(ticksStr, ticksObj, unitsType) {
                var ticksBlobs, tempFloat, tempTicks, c1, c2;

                // The 'ticks' setting is a string containing 3 floating-point
                // numbers.
                ticksBlobs = ticksStr.split(',');

                if (ticksBlobs.length !== 3) {
                    console.log('ERROR: Did not get 3 blobs from ticksStr = "' + ticksStr + '".');

                    return false;
                }

                tempFloat = parseFloat(ticksBlobs[0]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.min = tempFloat;
                } else {
                    console.log('ERROR: Invalid "min". ticksBlobs[0] = ', ticksBlobs[0]);

                    return false;
                }

                tempFloat = parseFloat(ticksBlobs[1]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.tickSize = tempFloat;
                } else {
                    console.log('ERROR: Invalid "tickSize". ticksBlobs[1] = ', ticksBlobs[1]);

                    return false;
                }

                tempFloat = parseFloat(ticksBlobs[2]);
                if (isNaN(tempFloat) === false) {
                    ticksObj.max = tempFloat;
                } else {
                    console.log('ERROR: Invalid "max". ticksBlobs[2] = ', ticksBlobs[2]);

                    return false;
                }

                // Is the starting tick to the left of the ending tick (on the
                // x-axis)? If not, set default starting and ending tick.
                if (ticksObj.min >= ticksObj.max) {
                    console.log('ERROR: Ticks min >= max.');

                    return false;
                }

                // Make sure the range makes sense - i.e. that there are at
                // least 3 ticks. If not, set a tickSize which will produce
                // 11 ticks. tickSize is the spacing between the ticks.
                if (ticksObj.tickSize > ticksObj.max - ticksObj.min) {
                    console.log('ERROR: tickSize > max - min.');

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
            var xRangeStr, xRangeBlobs, tempNum, allParamNames, funcString,
                disableAutoReturn;

            xrange = {};

            if ($.isPlainObject(config.plot.xrange) === false) {
                console.log(
                    'ERROR: Expected config.plot.xrange to be an object. ' +
                    'It is not.'
                );
                console.log('config.plot.xrange = ', config.plot.xrange);

                return false;
            }

            if (config.plot.xrange.hasOwnProperty('min') === false) {
                console.log(
                    'ERROR: Expected config.plot.xrange.min to be ' +
                    'present. It is not.'
                );

                return false;
            }

            disableAutoReturn = false;
            if (typeof config.plot.xrange.min === 'string') {
                funcString = config.plot.xrange.min;
            } else if (
                ($.isPlainObject(config.plot.xrange.min) === true) &&
                (config.plot.xrange.min.hasOwnProperty('#text') === true) &&
                (typeof config.plot.xrange.min['#text'] === 'string')
            ) {
                funcString = config.plot.xrange.min['#text'];

                disableAutoReturn =
                    config.plot.xrange.min['@disable_auto_return'];
                if (
                    (disableAutoReturn === undefined) ||
                    (
                        (typeof disableAutoReturn === 'string') &&
                        (disableAutoReturn.toLowerCase() !== 'true')
                    )
                ) {
                    disableAutoReturn = false;
                } else {
                    disableAutoReturn = true;
                }
            } else {
                console.log(
                    'ERROR: Could not get a function definition for ' +
                    'xrange.min property.'
                );

                return false;
            }

            funcString = $('<div>').html(funcString).text();

            if (disableAutoReturn === false) {
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

            allParamNames = state.getAllParameterNames();

            allParamNames.push(funcString);
            try {
                xrange.min = Function.apply(null, allParamNames);
            } catch (err) {
                console.log(
                    'ERROR: could not create a function from the string "' +
                    funcString + '" for xrange.min.'
                );
                console.log('Error message: "' + err.message + '"');

                if (state.showDebugInfo) {
                    $('#' + gstId).html(
                        '<div style="color: red;">' + 'ERROR IN ' +
                        'XML: Could not create a function from the string "' +
                        funcString + '" for xrange.min.' + '</div>'
                    );
                    $('#' + gstId).append(
                        '<div style="color: red;">' + 'Error ' +
                        'message: "' + err.message + '".' + '</div>'
                    );
                }

                return false;
            }
            allParamNames.pop();

            if (config.plot.xrange.hasOwnProperty('max') === false) {
                console.log(
                    'ERROR: Expected config.plot.xrange.max to be ' +
                    'present. It is not.'
                );

                return false;
            }

            disableAutoReturn = false;
            if (typeof config.plot.xrange.max === 'string') {
                funcString = config.plot.xrange.max;
            } else if (
                ($.isPlainObject(config.plot.xrange.max) === true) &&
                (config.plot.xrange.max.hasOwnProperty('#text') === true) &&
                (typeof config.plot.xrange.max['#text'] === 'string')
            ) {
                funcString = config.plot.xrange.max['#text'];

                disableAutoReturn =
                    config.plot.xrange.max['@disable_auto_return'];
                if (
                    (disableAutoReturn === undefined) ||
                    (
                        (typeof disableAutoReturn === 'string') &&
                        (disableAutoReturn.toLowerCase() !== 'true')
                    )
                ) {
                    disableAutoReturn = false;
                } else {
                    disableAutoReturn = true;
                }
            } else {
                console.log(
                    'ERROR: Could not get a function definition for ' +
                    'xrange.max property.'
                );

                return false;
            }

            funcString = $('<div>').html(funcString).text();

            if (disableAutoReturn === false) {
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

            allParamNames.push(funcString);
            try {
                xrange.max = Function.apply(null, allParamNames);
            } catch (err) {
                console.log(
                    'ERROR: could not create a function from the string "' +
                    funcString + '" for xrange.max.'
                );
                console.log('Error message: "' + err.message + '"');

                if (state.showDebugInfo) {
                    $('#' + gstId).html(
                        '<div style="color: red;">' + 'ERROR IN ' +
                        'XML: Could not create a function from the string "' +
                        funcString + '" for xrange.max.' + '</div>'
                    );
                    $('#' + gstId).append(
                        '<div style="color: red;">' + 'Error message: "' +
                        err.message + '".' + '</div>'
                    );
                }

                return false;
            }
            allParamNames.pop();

            tempNum = parseInt(config.plot.num_points, 10);
            if (isFinite(tempNum) === false) {
                tempNum = plotDiv.width() / 5.0;
            }

            if (
                (tempNum < 2) &&
                (tempNum > 1000)
            ) {
                console.log(
                    'ERROR: Number of points is outside the allowed range ' +
                    '[2, 1000]'
                );
                console.log('config.plot.num_points = ' + tempNum);

                return false;
            }

            numPoints = tempNum;

            return true;
        }

        function createFunctions() {
            var c1;

            functions = [];

            if (typeof config.functions === 'undefined') {
                console.log('ERROR: config.functions is undefined.');

                return;
            }

            if (typeof config.functions["function"] === 'string') {

                // If just one function string is present.
                addFunction(config.functions["function"]);

            } else if ($.isPlainObject(config.functions["function"]) === true) {

                // If a function is present, but it also has properties
                // defined.
                callAddFunction(config.functions["function"]);

            } else if ($.isArray(config.functions["function"])) {

                // If more than one function is defined.
                for (c1 = 0; c1 < config.functions["function"].length; c1 += 1) {

                    // For each definition, we must check if it is a simple
                    // string definition, or a complex one with properties.
                    if (typeof config.functions["function"][c1] === 'string') {

                        // Simple string.
                        addFunction(config.functions["function"][c1]);

                    } else if ($.isPlainObject(config.functions["function"][c1])) {

                        // Properties are present.
                        callAddFunction(config.functions["function"][c1]);

                    }
                }
            } else {
                console.log('ERROR: config.functions.function is of an unsupported type.');

                return;
            }

            return;

            // This function will reduce code duplication. We have to call
            // the function addFunction() several times passing object
            // properties as parameters. Rather than writing them out every
            // time, we will have a single place where it is done.
            function callAddFunction(obj) {
                if (
                    (obj.hasOwnProperty('@output')) &&
                    (typeof obj['@output'] === 'string')
                ) {

                    // If this function is meant to be calculated for an
                    // element then skip it.
                    if ((obj['@output'].toLowerCase() === 'element') ||
                        (obj['@output'].toLowerCase() === 'none')) {
                        return;
                    }

                    // If this function is meant to be calculated for a
                    // dynamic element in a label then skip it.
                    else if (obj['@output'].toLowerCase() === 'plot_label') {
                        return;
                    }

                    // It is an error if '@output' is not 'element',
                    // 'plot_label', or 'graph'. However, if the '@output'
                    // attribute is omitted, we will not have reached this.
                    else if (obj['@output'].toLowerCase() !== 'graph') {
                        console.log(
                            'ERROR: Function "output" attribute can be ' +
                            'either "element", "plot_label", "none" or "graph".'
                        );

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
                    obj['@bar'],
                    obj['@disable_auto_return']
                );
            }

            function addFunction(funcString, color, line, dot, label,
                pointSize, fillArea, bar, disableAutoReturn) {

                var newFunctionObject, func, paramNames, c1, rgxp;

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

                // If the user did not specifically turn off this feature,
                // check if the function string contains a 'return', and
                // prepend a 'return ' to the string if one, or more, is not
                // found.
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
                    console.log(
                        'ERROR: The function body "' +
                        funcString +
                        '" was not converted by the Function constructor.'
                    );
                    console.log('Error message: "' + err.message + '"');

                    if (state.showDebugInfo) {
                        $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not create a function from the string "' + funcString + '".' + '</div>');
                        $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');
                    }

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
                    // To do: See if need to do anything here.
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
                            console.log('ERROR: The attribute fill_area should be either "true" or "false".');
                            console.log('fill_area = "' + fillArea + '".');

                            return;
                        }
                    }
                }

                if (typeof label === 'string') {

                    newFunctionObject.specialLabel = false;
                    newFunctionObject.pldeHash = [];

                    // Let's check the label against all of the plde objects.
                    // plde is an abbreviation for Plot Label Dynamic Elements.
                    for (c1 = 0; c1 < state.plde.length; c1 += 1) {
                        rgxp = new RegExp(state.plde[c1].elId, 'g');

                        // If we find a dynamic element in the label, we will
                        // hash the current plde object, and indicate that this
                        // is a special label.
                        if (rgxp.test(label) === true) {
                            newFunctionObject.specialLabel = true;
                            newFunctionObject.pldeHash.push(state.plde[c1]);
                        }
                    }

                    newFunctionObject.label = label;
                } else {
                    newFunctionObject.label = false;
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
            var c0, c1, c3, functionObj, seriesObj, dataPoints, paramValues, x, y,
                start, end, step, numNotUndefined;

            paramValues = state.getAllParameterValues();

            dataSeries = [];

            for (c0 = 0; c0 < functions.length; c0 += 1) {
                functionObj = functions[c0];

                try {
                    start = xrange.min.apply(window, paramValues);
                } catch (err) {
                    console.log('ERROR: Could not determine xrange start.');
                    console.log('Error message: "' + err.message + '".');

                    if (state.showDebugInfo) {
                        $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not determine xrange start from defined function.' + '</div>');
                        $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');
                    }

                    return false;
                }
                try {
                    end = xrange.max.apply(window, paramValues);
                } catch (err) {
                    console.log('ERROR: Could not determine xrange end.');
                    console.log('Error message: "' + err.message + '".');

                    if (state.showDebugInfo) {
                        $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not determine xrange end from defined function.' + '</div>');
                        $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');
                    }

                    return false;
                }

                seriesObj = {};
                dataPoints = [];

                // For counting number of points added. In the end we will
                // compare this number to 'numPoints' specified in the config
                // JSON.
                c1 = 0;

                step = (end - start) / (numPoints - 1);

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
                        console.log('ERROR: Could not generate data.');
                        console.log('Error message: "' + err.message + '".');

                        if (state.showDebugInfo) {
                            $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not generate data from defined function.' + '</div>');
                            $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');
                        }

                        return false;
                    }

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
                    try {
                        y = functionObj.func.apply(window, paramValues);
                    } catch (err) {
                        console.log('ERROR: Could not generate data.');
                        console.log('Error message: "' + err.message + '".');

                        if (state.showDebugInfo) {
                            $('#' + gstId).html('<div style="color: red;">' + 'ERROR IN XML: Could not generate data from function.' + '</div>');
                            $('#' + gstId).append('<div style="color: red;">' + 'Error message: "' + err.message + '".' + '</div>');
                        }

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
                if (functionObj.label !== false) {
                    if (functionObj.specialLabel === true) {
                        (function (c1) {
                            var tempLabel;

                            tempLabel = functionObj.label;

                            while (c1 < functionObj.pldeHash.length) {
                                tempLabel = tempLabel.replace(
                                    functionObj.pldeHash[c1].elId,
                                    functionObj.pldeHash[c1].func.apply(
                                        window,
                                        state.getAllParameterValues()
                                    )
                                );

                                c1 += 1;
                            }

                            seriesObj.label = tempLabel;
                        }(0));
                    } else {
                        seriesObj.label = functionObj.label;
                    }
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
                    'barWidth': graphBarWidth
                };

                if (graphBarAlign !== null) {
                    seriesObj.bars.align = graphBarAlign;
                }

                if (functionObj.hasOwnProperty('pointSize')) {
                    seriesObj.points.radius = functionObj.pointSize;
                }

                // Add the newly created series object to the series set which
                // will be plotted by Flot.
                dataSeries.push(seriesObj);
            }

            if (graphBarAlign === null) {
                for (c0 = 0; c0 < numPoints; c0 += 1) {
                    // Number of points that have a value other than 'undefined' (undefined).
                    numNotUndefined = 0;

                    for (c1 = 0; c1 < dataSeries.length; c1 += 1) {
                        if (dataSeries[c1].bars.show === false) {
                            continue;
                        }

                        if (isFinite(parseInt(dataSeries[c1].data[c0][1])) === true) {
                            numNotUndefined += 1;
                        }
                    }

                    c3 = 0;
                    for (c1 = 0; c1 < dataSeries.length; c1 += 1) {
                        if (dataSeries[c1].bars.show === false) {
                            continue;
                        }

                        dataSeries[c1].data[c0][0] -= graphBarWidth * (0.5 * numNotUndefined - c3);

                        if (isFinite(parseInt(dataSeries[c1].data[c0][1])) === true) {
                            c3 += 1;
                        }
                    }
                }
            }

            for (c0 = 0; c0 < asymptotes.length; c0 += 1) {

                // If the user defined a label for this asympote, then the
                // property 'label' will be a string (in the other case it is
                // a boolean value 'false'). We will create an empty data set,
                // and add to it a label. This solution is a bit _wrong_ , but
                // it will have to do for now. Flot JS does not provide a way
                // to add labels to markings, and we use markings to generate
                // asymptotes.
                if (asymptotes[c0].label !== false) {
                    dataSeries.push({
                        'data': [],
                        'label': asymptotes[c0].label,
                        'color': asymptotes[c0].color
                    });
                }

            }

            return true;
        } // End-of: function generateData

        function updatePlot() {
            var paramValues, plotObj;

            paramValues = state.getAllParameterValues();

            if (xaxis.tickFormatter !== null) {
                xaxis.ticks = null;
            }

            if (yaxis.tickFormatter !== null) {
                yaxis.ticks = null;
            }

            // Tell Flot to draw the graph to our specification.
            plotObj = $.plot(
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

            updateMovingLabels();

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

            function updateMovingLabels() {
                var c1, labelCoord, pointOffset;

                for (c1 = 0; c1 < movingLabels.length; c1 += 1) {
                    if (movingLabels[c1].el === null) {
                        movingLabels[c1].el = $(
                            '<div>' +
                                movingLabels[c1].labelText +
                            '</div>'
                        );
                        movingLabels[c1].el.css('position', 'absolute');
                        movingLabels[c1].el.css('color', movingLabels[c1].fontColor);
                        movingLabels[c1].el.css('font-weight', movingLabels[c1].fontWeight);
                        movingLabels[c1].el.appendTo(plotDiv);

                        movingLabels[c1].elWidth = movingLabels[c1].el.width();
                        movingLabels[c1].elHeight = movingLabels[c1].el.height();
                    } else {
                        movingLabels[c1].el.detach();
                        movingLabels[c1].el.appendTo(plotDiv);
                    }

                    labelCoord = movingLabels[c1].func.apply(window, paramValues);

                    pointOffset = plotObj.pointOffset({'x': labelCoord.x, 'y': labelCoord.y});

                    movingLabels[c1].el.css('left', pointOffset.left - 0.5 * movingLabels[c1].elWidth);
                    movingLabels[c1].el.css('top', pointOffset.top - 0.5 * movingLabels[c1].elHeight);
                }
            }

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
                        console.log('ERROR: Could not generate value from asymptote function.');
                        console.log('Error message: ', err.message);

                        continue;
                    }

                    if (asymptote.type === 'x') {
                        markings.push({
                            'color': asymptote.color,
                            'lineWidth': 2,
                            'xaxis': {
                                'from': val,
                                'to': val
                            }
                        });
                    } else {
                        markings.push({
                            'color': asymptote.color,
                            'lineWidth': 2,
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

        function xAxisTickFormatter(val, axis) {
            if (xTicksNames.hasOwnProperty(val.toFixed(axis.tickDecimals)) === true) {
                return xTicksNames[val.toFixed(axis.tickDecimals)];
            }

            return '';
        }

        function yAxisTickFormatter(val, axis) {
            if (yTicksNames.hasOwnProperty(val.toFixed(axis.tickDecimals)) === true) {
                return yTicksNames[val.toFixed(axis.tickDecimals)];
            }

            return '';
        }
    }


});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
