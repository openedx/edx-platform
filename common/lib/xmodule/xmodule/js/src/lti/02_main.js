(function (requirejs, require, define) {

// In the case when the LTI constructor will be called before
// RequireJS finishes loading all of the LTI dependencies, we will have
// a mock function that will collect all the elements that must be
// initialized as LTI elements.
//
// Once RequireJS will load all of the necessary dependencies, main code
// will invoke the mock function with the second parameter set to truthy value.
// This will trigger the actual LTI constructor on all elements that
// are stored in a temporary list.
window.LTI = (function () {
    // Temporary storage place for elements that must be initialized as LTI
    // elements.
    var tempCallStack = [];

    return function (element, processTempCallStack) {
        // If mock function was called with second parameter set to truthy
        // value, we invoke the real `window.LTI` on all the stored elements
        // so far.
        if (processTempCallStack) {
            $.each(tempCallStack, function (index, element) {
                // By now, `window.LTI` is the real constructor.
                window.LTI(element);
            });

            return;
        }

        // If normal call to `window.LTI` constructor, store the element
        // for later initializing.
        tempCallStack.push(element);

        // Real LTI constructor returns `undefined`. The mock constructor will
        // return the same value. Making this explicit.
        return undefined;
    };
}());

// Main module.
require(
[
    'lti/01_lti.js'
],
function (
    LTIConstructor
) {
    var oldLTI = window.LTI;

    window.LTI = LTIConstructor;

    // Invoke the mock LTI constructor so that the elements stored within
    // it can be processed by the real `window.LTI` constructor.
    oldLTI(null, true);
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
