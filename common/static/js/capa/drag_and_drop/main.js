// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(
    ['logme', 'state', 'config_parser', 'target', 'draggables'],
    function (logme, State, configParser, Target, raggables) {
    return Main;

    function Main() {
        $('.drag_and_drop_problem').each(processProblem);
    }

    // $(value) - get the element of the entire problem
    function processProblem(index, value) {
        var problemId, config, state;

        problemId = $(value).attr('data-plain-id');
        if (typeof problemId !== 'string') {
            logme('ERROR: Could not find a problem DOM element ID.');

            return;
        }

        try {
            config = JSON.parse($(value).html());
        } catch (err) {
            logme('ERROR: Could not parse the JSON configuration options.');
            logme('Error message: "' + err.message + '".');

            return;
        }

        state = State(problemId);

        configParser(config, state);

        // Container(state);
        Target(state);
        // Scroller(state);
        Draggables(state);

        logme(state);
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
