// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define(
    'GstMain',

    // Even though it is not explicitly in this module, we have to specify
    // 'GeneralMethods' as a dependency. It expands some of the core JS objects
    // with additional useful methods that are used in other modules.
    ['State', 'GeneralMethods', 'Sliders', 'Inputs', 'Graph', 'ElOutput', 'GLabelElOutput', 'logme'],
    function (State, GeneralMethods, Sliders, Inputs, Graph, ElOutput, GLabelElOutput, logme) {

    return GstMain;

    function GstMain(gstId) {
        var config, gstClass, state;

        if ($('#' + gstId).attr('data-processed') !== 'processed') {
            $('#' + gstId).attr('data-processed', 'processed');
        } else {
            // logme('MESSAGE: Already processed GST with ID ' + gstId + '. Skipping.');

            return;
        }

        // Get the JSON configuration, parse it, and store as an object.
        try {
            config = JSON.parse($('#' + gstId + '_json').html()).root;
        } catch (err) {
            logme('ERROR: could not parse config JSON.');
            logme('$("#" + gstId + "_json").html() = ', $('#' + gstId + '_json').html());
            logme('JSON.parse(...) = ', JSON.parse($('#' + gstId + '_json').html()));
            logme('config = ', config);

            return;
        }

        // Get the class name of the GST. All elements are assigned a class
        // name that is based on the class name of the GST. For example, inputs
        // are assigned a class name '{GST class name}_input'.
        if (typeof config['@class'] !== 'string') {
            logme('ERROR: Could not get the class name of GST.');
            logme('config["@class"] = ', config['@class']);

            return;
        }
        gstClass = config['@class'];

        // Parse the configuration settings for parameters, and store them in a
        // state object.
        state = State(gstId, config);

        state.showDebugInfo = false;

        // It is possible that something goes wrong while extracting parameters
        // from the JSON config object. In this case, we will not continue.
        if (state === undefined) {
            logme('ERROR: The state object was not initialized properly.');

            return;
        }

        // Create the sliders and the text inputs, attaching them to
        // appropriate parameters.
        Sliders(gstId, state);
        Inputs(gstId, gstClass, state);

        // Configure functions that output to an element instead of the graph.
        ElOutput(config, state);

        // Configure functions that output to an element instead of the graph
        // label.
        GLabelElOutput(config, state);

        // Configure and display the graph. Attach event for the graph to be
        // updated on any change of a slider or a text input.
        Graph(gstId, config, state);
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
