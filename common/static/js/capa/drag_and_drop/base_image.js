// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return BaseImage;

    function BaseImage(state) {
        var targetImgSrc, baseImageElContainer, mouseMoveDiv;

        targetImgSrc = state.config.imageDir + '/' + state.config.base_image;

        baseImageElContainer = $(
            '<div ' +
                'class="base_image_container" ' +
                'style=" ' +
                    'position: relative; ' +
                '" ' +
            '></div>'
        );

        state.baseImageEl = $(
            '<img ' +
                'src="' + targetImgSrc + '" ' +
            '/>'
        );
        state.baseImageEl.appendTo(baseImageElContainer);

        state.baseImageElWidth = null;
        $('<img/>') // Make in memory copy of image to avoid css issues.
            .attr('src', state.baseImageEl.attr('src'))
            .load(function () {
                state.baseImageElWidth = this.width;
            });

        // state.baseImageEl.mousemove(
        //     function (event) {
        //         mouseMoveDiv.html(
        //             '[' + event.offsetX + ', ' + event.offsetY + ']'
        //         );
        //     }
        // );

        mouseMoveDiv = $(
            '<div ' +
                'style=" ' +
                    'clear: both; ' +
                    'width: auto; ' +
                    'height: 25px; ' +
                    'text-align: center; ' +
                '" ' +
            '></div>'
        );
        mouseMoveDiv.appendTo(baseImageElContainer);

        baseImageElContainer.appendTo(state.containerEl);
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
