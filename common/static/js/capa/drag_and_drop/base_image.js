(function (requirejs, require, define) {
define([], function () {
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

        state.baseImageEl = $('<img />', {
                alt: gettext("Drop target image")
            });

        state.baseImageEl.attr('src', state.config.baseImage);
        state.baseImageEl.load(function () {
            baseImageElContainer.css({
                'width': this.width,
                'height': this.height
            });

            state.baseImageEl.appendTo(baseImageElContainer);
            baseImageElContainer.appendTo(state.containerEl);

            state.baseImageEl.mousedown(function (event) {
                event.preventDefault();
            });

            state.baseImageLoaded = true;
        });
        state.baseImageEl.error(function () {
            console.log('ERROR: Image "' + state.config.baseImage + '" was not found!');
            baseImageElContainer.html(
                '<span style="color: red;">' +
                    'ERROR: Image "' + state.config.baseImage + '" was not found!' +
                '</span>'
            );
            baseImageElContainer.appendTo(state.containerEl);
        });
    }
}); // End-of: define([], function () {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define) {
