// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define(
    'GstMain',

    // Even though it is not explicitly in this module, we have to specify
    // 'GeneralMethods' as a dependency. It expands some of the core JS objects
    // with additional useful methods that are used in other modules.
    ['State', 'GeneralMethods', 'Sliders', 'Inputs', 'Graph', 'logme'],
    function (State, GeneralMethods, Sliders, Inputs, Graph, logme) {

    return GstMain;

    function GstMain(gstId) {
        var config, gstClass, state;

        // Get the JSON configuration, and parse it, and store as an object.
        config = JSON.parse($('#' + gstId + '_json').html()).root;

        gstClass = config['@class'];
        logme('gstClass: ' + gstClass);

        // Parse the configuration settings for sliders and text inputs, and
        // extract all of the defined constants (their names along with their
        // initial values).
        state = State(gstId, gstClass, config);

        // Create the sliders and the text inputs, attaching them to
        // approriate constants.
        Sliders(gstId, gstClass, state);
        Inputs(gstId, gstClass, state);

        // Configure and display the loop. Attach event for the graph to be
        // updated on any change of a slider or a text input.
        Graph(gstId, config, state);
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
