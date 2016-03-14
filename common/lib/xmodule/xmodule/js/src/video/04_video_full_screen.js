(function (define) {
'use strict';
define('video/04_video_full_screen.js', [], function () {
    var template = [
        '<button class="control add-fullscreen" aria-disabled="false">',
            '<span class="icon-fallback-img">',
                '<span class="icon fa fa-arrows-alt" aria-hidden="true"></span>',
                '<span class="sr control-text">',
                    gettext('Fill browser'),
                '</span>',
            '</span>',
        '</button>'
    ].join('');

    // VideoControl() function - what this module "exports".
    return function (state) {
        var dfd = $.Deferred();

        state.videoFullScreen = {};

        _makeFunctionsPublic(state);
        _renderElements(state);
        _bindHandlers(state);

        dfd.resolve();
        return dfd.promise();
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function _makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function _makeFunctionsPublic(state) {
        var methodsDict = {
            destroy: destroy,
            enter: enter,
            exitHandler: exitHandler,
            exit: exit,
            onFullscreenChange: onFullscreenChange,
            toggle: toggle,
            toggleHandler: toggleHandler,
            updateControlsHeight: updateControlsHeight
        };

        state.bindTo(methodsDict, state.videoFullScreen, state);
    }

    function destroy() {
        $(document).off('keyup', this.videoFullScreen.exitHandler);
        this.videoFullScreen.fullScreenEl.remove();
        this.el.off({
            'fullscreen': this.videoFullScreen.onFullscreenChange,
            'destroy': this.videoFullScreen.destroy
        });
        if (this.isFullScreen) {
            this.videoFullScreen.exit();
        }
        delete this.videoFullScreen;
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function _renderElements(state) {
        state.videoFullScreen.fullScreenEl = $(template);
        state.videoFullScreen.sliderEl = state.el.find('.slider');
        state.videoFullScreen.fullScreenState = false;
        state.el.find('.secondary-controls').append(state.videoFullScreen.fullScreenEl);
        state.videoFullScreen.updateControlsHeight();
    }

    // function _bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function _bindHandlers(state) {
        state.videoFullScreen.fullScreenEl.on('click', state.videoFullScreen.toggleHandler);
        state.el.on({
            'fullscreen': state.videoFullScreen.onFullscreenChange,
            'destroy': state.videoFullScreen.destroy
        });
        $(document).on('keyup', state.videoFullScreen.exitHandler);
    }

    function _getControlsHeight(controls, slider) {
        return controls.height() + 0.5 * slider.height();
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function onFullscreenChange (event, isFullScreen) {
        var height = this.videoFullScreen.updateControlsHeight();

        if (isFullScreen) {
            this.resizer
                .delta
                .substract(height, 'height')
                .setMode('both');

        } else {
            this.resizer
                .delta
                .reset()
                .setMode('width');
        }
    }

    function updateControlsHeight() {
        var controls = this.el.find('.video-controls'),
            slider = this.videoFullScreen.sliderEl;
        this.videoFullScreen.height = _getControlsHeight(controls, slider);
        return this.videoFullScreen.height;
    }

    /**
     * Event handler to toggle fullscreen mode.
     * @param {jquery Event} event
     */
    function toggleHandler(event) {
        event.preventDefault();
        this.videoCommands.execute('toggleFullScreen');
    }

    function exit() {
        var fullScreenClassNameEl = this.el.add(document.documentElement);

        this.videoFullScreen.fullScreenState = this.isFullScreen = false;
        fullScreenClassNameEl.removeClass('video-fullscreen');
        $(window).scrollTop(this.scrollPos);
        this.videoFullScreen.fullScreenEl
            .find('.icon')
                .removeClass('fa-compress')
                .addClass('fa-arrows-alt')
                .find('.control-text')
                    .text(gettext('Fill browser'));

        this.el.trigger('fullscreen', [this.isFullScreen]);
    }

    function enter() {
        var fullScreenClassNameEl = this.el.add(document.documentElement);

        this.scrollPos = $(window).scrollTop();
        $(window).scrollTop(0);
        this.videoFullScreen.fullScreenState = this.isFullScreen = true;
        fullScreenClassNameEl.addClass('video-fullscreen');
        this.videoFullScreen.fullScreenEl
            .find('.icon')
                .removeClass('fa-arrows-alt')
                .addClass('fa-compress')
                .find('.control-text')
                    .text(gettext('Exit full browser'));

        this.el.trigger('fullscreen', [this.isFullScreen]);
    }

    /** Toggle fullscreen mode. */
    function toggle() {
        if (this.videoFullScreen.fullScreenState) {
            this.videoFullScreen.exit();
        } else {
            this.videoFullScreen.enter();
        }
    }

    /**
     * Event handler to exit from fullscreen mode.
     * @param {jquery Event} event
     */
    function exitHandler(event) {
        if ((this.isFullScreen) && (event.keyCode === 27)) {
            event.preventDefault();
            this.videoCommands.execute('toggleFullScreen');
        }
    }
});

}(RequireJS.define));
