// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return BaseImage;

    function BaseImage(state) {
        var baseImageElContainer;

        baseImageElContainer = $(
            '<div ' +
                'class="base_image_container" ' +
                'style=" ' +
                    'position: relative; ' +
                    'margin-bottom: 25px; ' +
                    'margin-left: auto; ' +
                    'margin-right: auto; ' +
                '" ' +
            '></div>'
        );

        state.baseImageEl = $('<img />');

        state.baseImageEl.attr(
            'src',
            state.config.base_image
        );
        state.baseImageEl.load(function () {
            baseImageElContainer.css('width', this.width);
            baseImageElContainer.css('height', this.height);

            state.baseImageEl.appendTo(baseImageElContainer);
            baseImageElContainer.appendTo(state.containerEl);

            state.baseImageLoaded = true;
        });
        state.baseImageEl.error(function () {
            logme(
                'ERROR: Image "' + state.config.base_image + '" was not found!'
            );
            baseImageElContainer.html(
                '<span style="color: red;">' +
                    'ERROR: Image "' + state.config.base_image + '" was not found!' +
                '</span>'
            );
            baseImageElContainer.appendTo(state.containerEl);
        });
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
