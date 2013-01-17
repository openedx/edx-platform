/*
 * We will add a function that will be called for all GraphicalSliderTool
 * xmodule module instances. It must be available globally by design of
 * xmodule.
 */
window.GraphicalSliderTool = function (el) {
    // All the work will be performed by the GstMain module. We will get access
    // to it, and all it's dependencies, via Require JS. Currently Require JS
    // is namespaced and is available via a global object RequireJS.
    RequireJS.require(['GstMain'], function (GstMain) {
        // The GstMain module expects the DOM ID of a Graphical Slider Tool
        // element. Since we are given a <section> element which might in
        // theory contain multiple graphical_slider_tool <div> elements (each
        // with a unique DOM ID), we will iterate over all children, and for
        // each match, we will call GstMain module.
        $(el).children('.graphical_slider_tool').each(function (index, value) {
            JavascriptLoader.executeModuleScripts($(value), function(){
                GstMain($(value).attr('id'));
            });
        });
    });
};
