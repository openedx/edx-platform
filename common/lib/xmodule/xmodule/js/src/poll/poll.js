/*
 * We will add a function that will be called for all Poll
 * xmodule module instances. It must be available globally by design of
 * xmodule.
 */
window.Poll = function (el) {
    // All the work will be performed by the PollMain module. We will get access
    // to it, and all it's dependencies, via Require JS. Currently Require JS
    // is namespaced and is available via a global object RequireJS.
    RequireJS.require(['PollMain'], function (PollMain) {
        // The PollMain module expects the DOM ID of a Poll
        // element. Since we are given a <section> element which might in
        // theory contain multiple Poll <div> elements (each
        // with a unique DOM ID), we will iterate over all children, and for
        // each match, we will call GstMain module.
        $(el).children('.poll').each(function (index, value) {
            console.log('inpoll');
            console.log($(value));
            var tmp = new PollMain($(value));
        });
    });
};
