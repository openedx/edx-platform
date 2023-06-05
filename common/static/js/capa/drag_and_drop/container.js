(function(requirejs, require, define) {
    define(['edx-ui-toolkit/js/utils/html-utils'], function(HtmlUtils) {
        return Container;

        function Container(state) {
            state.containerEl = $(
                '<div style=" clear: both; width: 665px; margin-left: auto; margin-right: auto; " ></div>'
            );

            $('#inputtype_' + state.problemId).before(HtmlUtils.HTML(state.containerEl).toString());
        }
    }); // End-of: define([], function () {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define) {
