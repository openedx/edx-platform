(function (requirejs, require, define) {

// VideoSpeedControl module.
define(
'video/08_video_speed_control.js',
[],
function () {

    // VideoSpeedControl() function - what this module "exports".
    return function (state) {
        var dfd = $.Deferred();

        if (state.isTouch) {
            // iOS doesn't support speed change
            state.el.find('div.speeds').remove();
            dfd.resolve();
            return dfd.promise();
        }

        state.videoSpeedControl = {};

        _initialize(state);
        dfd.resolve();

        if (state.videoType === 'html5' && !(_checkPlaybackRates())) {
            console.log(
                '[Video info]: HTML5 mode - playbackRate is not supported.'
            );

            _hideSpeedControl(state);
        }

        return dfd.promise();
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    function _initialize(state) {
        _makeFunctionsPublic(state);
        _renderElements(state);
        _bindHandlers(state);
    }

    // function _makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called,
    //     these functions will get the 'state' object as a context.
    function _makeFunctionsPublic(state) {
        var methodsDict = {
            changeVideoSpeed: changeVideoSpeed,
            reRender: reRender,
            setSpeed: setSpeed
        };

        state.bindTo(methodsDict, state.videoSpeedControl, state);
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their
    //     initial configuration. Also make the created DOM elements available
    //     via the 'state' object. Much easier to work this way - you don't
    //     have to do repeated jQuery element selects.
    function _renderElements(state) {
        state.videoSpeedControl.speeds = state.speeds;

        state.videoSpeedControl.el = state.el.find('div.speeds');

        state.videoSpeedControl.videoSpeedsEl = state.videoSpeedControl.el
            .find('.video_speeds');

        state.videoControl.secondaryControlsEl.prepend(
            state.videoSpeedControl.el
        );

        $.each(state.videoSpeedControl.speeds, function (index, speed) {
            var link = '<a class="speed_link" href="#">' + speed + 'x</a>';

            state.videoSpeedControl.videoSpeedsEl
                .prepend(
                    $('<li data-speed="' + speed + '">' + link + '</li>')
                );
        });

        state.videoSpeedControl.setSpeed(state.speed);
    }

    /**
     * @desc Check if playbackRate supports by browser.
     *
     * @type {function}
     * @access private
     *
     * @param {object} state The object containg the state of the video player.
     *     All other modules, their parameters, public variables, etc. are
     *     available via this object.
     *
     * @this {object} The global window object.
     *
     * @returns {Boolean}
     *       true: Browser support playbackRate functionality.
     *       false: Browser doesn't support playbackRate functionality.
     */
    function _checkPlaybackRates() {
        var video = document.createElement('video');

        // If browser supports, 1.0 should be returned by playbackRate
        // property. In this case, function return True. Otherwise, False will
        // be returned.
        return Boolean(video.playbackRate);
    }

    // Hide speed control.
    function _hideSpeedControl(state) {
        state.el.find('div.speeds').hide();
    }

    // Get previous element in array or cyles back to the last if it is the
    // first.
    function _previousSpeedLink(speedLinks, index) {
        return $(speedLinks.eq(index < 1 ? speedLinks.length - 1 : index - 1));
    }

    // Get next element in array or cyles back to the first if it is the last.
    function _nextSpeedLink(speedLinks, index) {
        return $(speedLinks.eq(index >= speedLinks.length - 1 ? 0 : index + 1));
    }

    function _speedLinksFocused(state) {
        var speedLinks = state.videoSpeedControl.videoSpeedsEl
                                                .find('a.speed_link');
        return speedLinks.is(':focus');
    }

    function _openMenu(state) {
        // When speed entries have focus, the menu stays open on
        // mouseleave. A clickHandler is added to the window
        // element to have clicks close the menu when they happen
        // outside of it.
        $(window).on('click.speedMenu', _clickHandler.bind(state));
        state.videoSpeedControl.el.addClass('open');
    }

    function _closeMenu(state) {
        // Remove the previously added clickHandler from window element.
        $(window).off('click.speedMenu');
        state.videoSpeedControl.el.removeClass('open');
    }

    // Various event handlers. They all return false to stop propagation and
    // prevent default behavior.
    function _clickHandler(event) {
        var target = $(event.currentTarget);

        this.videoSpeedControl.el.removeClass('open');
        if (target.is('a.speed_link')) {
            this.videoSpeedControl.changeVideoSpeed.call(this, event);
        }

        return false;
    }

    // We do not use _openMenu and _closeMenu in the following two handlers
    // because we do not want to add an unnecessary clickHandler to the window
    // element.
    function _mouseEnterHandler(event) {
        this.videoSpeedControl.el.addClass('open');

        return false;
    }

    function _mouseLeaveHandler(event) {
        // Only close the menu is no speed entry has focus.
        if (!_speedLinksFocused(this)) {
            this.videoSpeedControl.el.removeClass('open');
        }
                
        return false;
    }

    function _keyDownHandler(event) {
        var KEY = $.ui.keyCode,
            keyCode = event.keyCode,
            target = $(event.currentTarget),
            speedButtonLink = this.videoSpeedControl.el.children('a'),
            speedLinks = this.videoSpeedControl.videoSpeedsEl
                                               .find('a.speed_link'),
            index;

        if (target.is('a.speed_link')) {

            index = target.parent().index();

            switch (keyCode) {
                // Scroll up menu, wrapping at the top. Keep menu open.
                case KEY.UP:
                    _previousSpeedLink(speedLinks, index).focus();
                    break;
                // Scroll down  menu, wrapping at the bottom. Keep menu
                // open.
                case KEY.DOWN:
                    _nextSpeedLink(speedLinks, index).focus();
                    break;
                // Close menu.
                case KEY.TAB:
                    _closeMenu(this);
                    // Set focus to previous menu button in menu bar
                    // (Play/Pause button)
                    if (event.shiftKey) {
                        this.videoControl.playPauseEl.focus();
                    }
                    // Set focus to next menu button in menu bar
                    // (Volume button)
                    else {
                        this.videoVolumeControl.buttonEl.focus();
                    }
                    break;
                // Close menu, give focus to speed control and change
                // speed.
                case KEY.ENTER:
                case KEY.SPACE:
                    _closeMenu(this);
                    speedButtonLink.focus();
                    this.videoSpeedControl.changeVideoSpeed.call(this, event);
                    break;
                // Close menu and give focus to speed control.
                case KEY.ESCAPE:
                    _closeMenu(this);
                    speedButtonLink.focus();
                    break;
            }
            return false;
        }
        else {
            switch(keyCode) {
                // Open menu and focus on last element of list above it.
                case KEY.ENTER:
                case KEY.SPACE:
                case KEY.UP:
                    _openMenu(this);
                    speedLinks.last().focus();
                    break;
                // Close menu.
                case KEY.ESCAPE:
                    _closeMenu(this);
                    break;
            }
            // We do not stop propagation and default behavior on a TAB
            // keypress.
            return event.keyCode === KEY.TAB;
        }
    }

    /**
     * @desc Bind any necessary function callbacks to DOM events (click,
     *     mousemove, etc.).
     *
     * @type {function}
     * @access private
     *
     * @param {object} state The object containg the state of the video player.
     *     All other modules, their parameters, public variables, etc. are
     *     available via this object.
     *
     * @this {object} The global window object.
     *
     * @returns {undefined}
     */
    function _bindHandlers(state) {
        var speedButton = state.videoSpeedControl.el,
            videoSpeeds = state.videoSpeedControl.videoSpeedsEl;

        // Attach various events handlers to the speed menu button.
        speedButton.on({
            'mouseenter': _mouseEnterHandler.bind(state),
            'mouseleave': _mouseLeaveHandler.bind(state),
            'click': _clickHandler.bind(state),
            'keydown': _keyDownHandler.bind(state)
        });

        // Attach click and keydown event handlers to the individual speed
        // entries.
        videoSpeeds.on('click', 'a.speed_link', _clickHandler.bind(state))
                   .on('keydown', 'a.speed_link', _keyDownHandler.bind(state));
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this'
    // keyword) is the 'state' object. The magic private function that makes
    // them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function setSpeed(speed) {
        this.videoSpeedControl.videoSpeedsEl.find('li').removeClass('active');
        this.videoSpeedControl.videoSpeedsEl
            .find("li[data-speed='" + speed + "']")
            .addClass('active');
        this.videoSpeedControl.el.find('p.active').html('' + speed + 'x');
    }

    function changeVideoSpeed(event) {
        var parentEl = $(event.target).parent();

        event.preventDefault();

        if (!parentEl.hasClass('active')) {
            this.videoSpeedControl.currentSpeed = parentEl.data('speed');

            this.videoSpeedControl.setSpeed(
                // To meet the API expected format.
                parseFloat(this.videoSpeedControl.currentSpeed)
                    .toFixed(2)
                    .replace(/\.00$/, '.0')
            );

            this.trigger(
                'videoPlayer.onSpeedChange',
                this.videoSpeedControl.currentSpeed
            );
        }
    }

    function reRender(params) {
        var _this = this;

        this.videoSpeedControl.videoSpeedsEl.empty();
        this.videoSpeedControl.videoSpeedsEl.find('li').removeClass('active');
        this.videoSpeedControl.speeds = params.newSpeeds;

        $.each(this.videoSpeedControl.speeds, function (index, speed) {
            var link, listItem;

            link = '<a class="speed_link" href="#" role="menuitem">' + speed + 'x</a>';

            listItem = $('<li data-speed="' + speed + '" role="presentation">' + link + '</li>');

            if (speed === params.currentSpeed) {
                listItem.addClass('active');
            }

            _this.videoSpeedControl.videoSpeedsEl.prepend(listItem);
        });

        // Re-attach all events with their appropriate callbacks to the
        // newly generated elements.
        _bindHandlers(this);
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
