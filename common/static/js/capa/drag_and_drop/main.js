// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(
    ['logme', 'state', 'config_parser', 'container', 'target', 'scroller', 'draggables'],
    function (logme, State, configParser, Container, Target, Scroller, Draggables) {
    return Main;

    function Main() {
        $('.drag_and_drop_problem_div').each(processProblem);
    }

    // $(value) - get the element of the entire problem
    function processProblem(index, value) {
        var problemId, imageDir, config, state;

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

        imageDir = $(value).attr('data-course-folder');
        if (typeof imageDir !== 'string') {
            logme('ERROR: Could not find the name of the image directory.');

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

        if (configParser(config, imageDir, state) !== true) {
            logme('ERROR: Could not make sense of the JSON configuration options.');

            return;
        }

        Container(state);
        Target(state);
        Scroller(state);
        Draggables(state);

        logme(state);
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
