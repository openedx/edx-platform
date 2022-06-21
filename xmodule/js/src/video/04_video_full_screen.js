(function(define) {
    'use strict';
    define('video/04_video_full_screen.js', ['edx-ui-toolkit/js/utils/html-utils'], function(HtmlUtils) {
        var template = [
            '<button class="control add-fullscreen" aria-disabled="false" title="',
            gettext('Fill browser'),
            '" aria-label="',
            gettext('Fill browser'),
            '">',
            '<span class="icon fa fa-arrows-alt" aria-hidden="true"></span>',
            '</button>'
        ].join('');

    // The following properties and functions enable cross-browser use of the
    // the Fullscreen Web API.
    //
    //     function getVendorPrefixed(property)
    //     function getFullscreenElement()
    //     function exitFullscreen()
    //     function requestFullscreen(element, options)
    //
    //     For more information about the Fullscreen Web API see MDN:
    //     https://developer.mozilla.org/en-US/docs/Web/API/Fullscreen_API
        var prefixedFullscreenProperties = (function() {
            if ('fullscreenEnabled' in document) {
                return {
                    fullscreenElement: 'fullscreenElement',
                    fullscreenEnabled: 'fullscreenEnabled',
                    requestFullscreen: 'requestFullscreen',
                    exitFullscreen: 'exitFullscreen',
                    fullscreenchange: 'fullscreenchange',
                    fullscreenerror: 'fullscreenerror'
                };
            }
            if ('webkitFullscreenEnabled' in document) {
                return {
                    fullscreenElement: 'webkitFullscreenElement',
                    fullscreenEnabled: 'webkitFullscreenEnabled',
                    requestFullscreen: 'webkitRequestFullscreen',
                    exitFullscreen: 'webkitExitFullscreen',
                    fullscreenchange: 'webkitfullscreenchange',
                    fullscreenerror: 'webkitfullscreenerror'
                };
            }
            if ('mozFullScreenEnabled' in document) {
                return {
                    fullscreenElement: 'mozFullScreenElement',
                    fullscreenEnabled: 'mozFullScreenEnabled',
                    requestFullscreen: 'mozRequestFullScreen',
                    exitFullscreen: 'mozCancelFullScreen',
                    fullscreenchange: 'mozfullscreenchange',
                    fullscreenerror: 'mozfullscreenerror'
                };
            }
            if ('msFullscreenEnabled' in document) {
                return {
                    fullscreenElement: 'msFullscreenElement',
                    fullscreenEnabled: 'msFullscreenEnabled',
                    requestFullscreen: 'msRequestFullscreen',
                    exitFullscreen: 'msExitFullscreen',
                    fullscreenchange: 'MSFullscreenChange',
                    fullscreenerror: 'MSFullscreenError'
                };
            }
            return {};
        }());

        function getVendorPrefixed(property) {
            return prefixedFullscreenProperties[property];
        }

        function getFullscreenElement() {
            return document[getVendorPrefixed('fullscreenElement')];
        }

        function exitFullscreen() {
            if (document[getVendorPrefixed('exitFullscreen')]) {
                return document[getVendorPrefixed('exitFullscreen')]();
            }
            return null;
        }

        function requestFullscreen(element, options) {
            if (element[getVendorPrefixed('requestFullscreen')]) {
                return element[getVendorPrefixed('requestFullscreen')](options);
            }
            return null;
        }

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

        function destroy() {
            $(document).off('keyup', this.videoFullScreen.exitHandler);
            this.videoFullScreen.fullScreenEl.remove();
            this.el.off({
                destroy: this.videoFullScreen.destroy
            });
            document.removeEventListener(
                getVendorPrefixed('fullscreenchange'),
                this.videoFullScreen.handleFullscreenChange
            );
            if (this.isFullScreen) {
                this.videoFullScreen.exit();
            }
            delete this.videoFullScreen;
        }

    // function renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
        function renderElements(state) {
            /* eslint-disable no-param-reassign */
            state.videoFullScreen.fullScreenEl = $(template);
            state.videoFullScreen.sliderEl = state.el.find('.slider');
            state.videoFullScreen.fullScreenState = false;
            HtmlUtils.append(state.el.find('.secondary-controls'), HtmlUtils.HTML(state.videoFullScreen.fullScreenEl));
            state.videoFullScreen.updateControlsHeight();
            /* eslint-enable no-param-reassign */
        }

    // function bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
        function bindHandlers(state) {
            state.videoFullScreen.fullScreenEl.on('click', state.videoFullScreen.toggleHandler);
            state.el.on({
                destroy: state.videoFullScreen.destroy
            });
            $(document).on('keyup', state.videoFullScreen.exitHandler);
            document.addEventListener(
                getVendorPrefixed('fullscreenchange'),
                state.videoFullScreen.handleFullscreenChange
            );
        }

        function getControlsHeight(controls, slider) {
            return controls.height() + 0.5 * slider.height();
        }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

        function handleFullscreenChange() {
            if (getFullscreenElement() !== this.el[0] && this.isFullScreen) {
                // The video was fullscreen so this event must relate to this video
                this.videoFullScreen.handleExit();
            }
        }

        function updateControlsHeight() {
            var controls = this.el.find('.video-controls'),
                slider = this.videoFullScreen.sliderEl;
            this.videoFullScreen.height = getControlsHeight(controls, slider);
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

        function handleExit() {
            var fullScreenClassNameEl = this.el.add(document.documentElement);
            var closedCaptionsEl = this.el.find('.closed-captions');

            if (this.isFullScreen === false) {
                return;
            }

            this.videoFullScreen.fullScreenState = this.isFullScreen = false;
            fullScreenClassNameEl.removeClass('video-fullscreen');
            $(window).scrollTop(this.scrollPos);
            this.videoFullScreen.fullScreenEl
            .attr({title: gettext('Fill browser'), 'aria-label': gettext('Fill browser')})
            .find('.icon')
                .removeClass('fa-compress')
                .addClass('fa-arrows-alt');

            $(closedCaptionsEl).css({top: '70%', left: '5%'});
            if (this.resizer) {
                this.resizer.delta.reset().setMode('width');
            }
            this.el.trigger('fullscreen', [this.isFullScreen]);
        }

        function handleEnter() {
            var fullScreenClassNameEl = this.el.add(document.documentElement);
            var closedCaptionsEl = this.el.find('.closed-captions');

            if (this.isFullScreen === true) {
                return;
            }

            this.videoFullScreen.fullScreenState = this.isFullScreen = true;
            fullScreenClassNameEl.addClass('video-fullscreen');
            this.videoFullScreen.fullScreenEl
            .attr({title: gettext('Exit full browser'), 'aria-label': gettext('Exit full browser')})
            .find('.icon')
                .removeClass('fa-arrows-alt')
                .addClass('fa-compress');

            $(closedCaptionsEl).css({top: '70%', left: '5%'});
            if (this.resizer) {
                this.resizer.delta.substract(this.videoFullScreen.updateControlsHeight(), 'height').setMode('both');
            }
            this.el.trigger('fullscreen', [this.isFullScreen]);
        }

        function exit() {
            if (getFullscreenElement() === this.el[0]) {
                exitFullscreen();
            } else {
                // Else some other element is fullscreen or the fullscreen api does not exist.
                this.videoFullScreen.handleExit();
            }
        }

        function enter() {
            this.scrollPos = $(window).scrollTop();
            this.videoFullScreen.handleEnter();
            requestFullscreen(this.el[0]);
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

    // function makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
        function makeFunctionsPublic(state) {
            var methodsDict = {
                destroy: destroy,
                enter: enter,
                exit: exit,
                exitHandler: exitHandler,
                handleExit: handleExit,
                handleEnter: handleEnter,
                handleFullscreenChange: handleFullscreenChange,
                toggle: toggle,
                toggleHandler: toggleHandler,
                updateControlsHeight: updateControlsHeight
            };

            state.bindTo(methodsDict, state.videoFullScreen, state);
        }

        // VideoControl() function - what this module "exports".
        return function(state) {
            var dfd = $.Deferred();

            // eslint-disable-next-line no-param-reassign
            state.videoFullScreen = {};

            makeFunctionsPublic(state);
            renderElements(state);
            bindHandlers(state);

            dfd.resolve();
            return dfd.promise();
        };
    });
}(RequireJS.define));
