(function (requirejs, require, define) {
define(
    ['logme', 'state', 'config_parser', 'container', 'base_image', 'scroller', 'draggables', 'targets', 'update_input'],
    function (logme, State, configParser, Container, BaseImage, Scroller, Draggables, Targets, updateInput) {
    return Main;

    function Main() {

        // https://developer.mozilla.org/en-US/docs/JavaScript/Reference/Global_Objects/Array/every
        //
        // Array.prototype.every is a recent addition to the ECMA-262 standard; as such it may not be present in
        // other implementations of the standard.
        if (!Array.prototype.every) {
            Array.prototype.every = function(fun /*, thisp */) {
                var thisp, t, len, i;

                if (this == null) {
                    throw new TypeError();
                }

                t = Object(this);
                len = t.length >>> 0;
                if (typeof fun != 'function') {
                    throw new TypeError();
                }

                thisp = arguments[1];

                for (i = 0; i < len; i++) {
                    if (i in t && !fun.call(thisp, t[i], i, t)) {
                        return false;
                    }
                }

                return true;
            };
        }

        $('.drag_and_drop_problem_div').each(processProblem);
    }

    // $(value) - get the element of the entire problem
    function processProblem(index, value) {
        var problemId, config, state;

        if ($(value).attr('data-problem-processed') === 'true') {
            // This problem was already processed by us before, so we will
            // skip it.

            return;
        }
        $(value).attr('data-problem-processed', 'true');

        problemId = $(value).attr('data-plain-id');
        if (typeof problemId !== 'string') {
            logme('ERROR: Could not find the ID of the problem DOM element.');

            return;
        }

        try {
            config = JSON.parse($('#drag_and_drop_json_' + problemId).html());
        } catch (err) {
            logme('ERROR: Could not parse the JSON configuration options.');
            logme('Error message: "' + err.message + '".');

            return;
        }

        state = State(problemId);

        if (configParser(state, config) !== true) {
            logme('ERROR: Could not make sense of the JSON configuration options.');

            return;
        }

        Container(state);
        BaseImage(state);

        (function addContent() {
            if (state.baseImageLoaded !== true) {
                setTimeout(addContent, 50);

                return;
            }

            Targets.initializeBaseTargets(state);
            Scroller(state);
            Draggables.init(state);

            state.updateArrowOpacity();

            // Update the input element, checking first that it is not filled with
            // an answer from the server.
            if (updateInput.check(state) === false) {
                updateInput.update(state);
            }
        }());
    }
}); // End-of: define(
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define) {
