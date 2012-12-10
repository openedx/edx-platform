// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define('Graph', ['logme'], function (logme) {

    return Graph;

    function Graph(gstId, state) {
        var plotDiv, data;
        logme('We are inside Graph module.', gstId, state);

        plotDiv = $('#' + gstId + '_plot');

        if (plotDiv.length === 0) {
            return;
        }

        plotDiv.width(300);
        plotDiv.height(300);

        state.bindUpdatePlotEvent(plotDiv, onUpdatePlot);

        generateData();
        updatePlot();

        return;

        function onUpdatePlot(event) {
            logme('redrawing plot');

            generateData();
            updatePlot();
        }

        function generateData() {
            var a, b, c1;

            a = state.getConstValue('a');
            b = state.getConstValue('b');

            data = [];
            data.push([]);

            for (c1 = 0; c1 < 30; c1++) {
                data[0].push([c1, a * c1 * (c1 + a)* (c1 - b) + b * c1 * (c1 + b * a)]);
            }
        }

        function updatePlot() {
            $.plot(plotDiv, data, {xaxis: {min: 0, max: 30}});
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
