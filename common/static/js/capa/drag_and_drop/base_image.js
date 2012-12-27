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
                '" ' +
            '></div>'
        );

        state.baseImageEl = $(
            '<img ' +
                'src="' + state.config.imageDir + '/' + state.config.base_image + '" ' +
            '/>'
        );
        state.baseImageEl.appendTo(baseImageElContainer);

        baseImageElContainer.appendTo(state.containerEl);
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
