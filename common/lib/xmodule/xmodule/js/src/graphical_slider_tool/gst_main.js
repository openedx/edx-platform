// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

define(
    'GstMain',
    ['State', 'GeneralMethods', 'Sliders', 'Inputs', 'Graph'],
    function (State, GeneralMethods, Sliders, Inputs, Graph) {

    return GstMain;

    function GstMain(gstId) {
        var config, state;

        config = JSON.parse($('#' + gstId + '_json').html()).root;

        state = State(gstId, config);

        Sliders(gstId, config, state);
        Inputs(gstId, config, state);

        Graph(gstId, config, state);
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
