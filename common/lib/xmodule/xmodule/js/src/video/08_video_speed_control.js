(function (requirejs, require, define) {
define(
'video/08_video_speed_control.js',
['video/00_iterator.js'],
function (Iterator) {
    "use strict";
    /**
     * Video speed control module.
     * @exports video/08_video_speed_control.js
     * @constructor
     * @param {object} state The object containing the state of the video player.
     * @return {jquery Promise}
     */
    var SpeedControl = function (state) {
        if (!(this instanceof SpeedControl)) {
            return new SpeedControl(state);
        }

        this.state = state;
        this.state.videoSpeedControl = this;
        this.initialize();

        return $.Deferred().resolve().promise();
    };

    SpeedControl.prototype = {
        /** Initializes the module. */
        initialize: function () {
            var state = this.state;

            this.el = state.el.find('.speeds');
            this.speedsContainer = this.el.find('.video-speeds');
            this.speedButton = this.el.find('.speed-button');

            if (!this.isPlaybackRatesSupported(state)) {
                this.el.remove();
                console.log(
                    '[Video info]: playbackRate is not supported.'
                );

                return false;
            }

            this.render(state.speeds, state.speed);
            this.bindHandlers();

            return true;
        },

        /**
         * Creates any necessary DOM elements, attach them, and set their,
         * initial configuration.
         * @param {array} speeds List of speeds available for the player.
         * @param {string|number} currentSpeed Current speed for the player.
         */
        render: function (speeds, currentSpeed) {
            var self = this,
                speedsContainer = this.speedsContainer,
                reversedSpeeds = speeds.concat().reverse(),
                speedsList = $.map(reversedSpeeds, function (speed, index) {
                    return [
                        '<li data-speed="', speed, '" role="presentation">',
                            '<a class="speed-link" href="#" role="menuitem" tabindex="-1">',
                                speed, 'x',
                            '</a>',
                        '</li>'
                    ].join('');
                });

            speedsContainer.html(speedsList.join(''));
            this.speedLinks = new Iterator(speedsContainer.find('.speed-link'));
            this.setSpeed(currentSpeed, true, true);
        },

        /**
         * Bind any necessary function callbacks to DOM events (click,
         * mousemove, etc.).
         */
        bindHandlers: function () {
            var self = this;

            // Attach various events handlers to the speed menu button.
            this.el.on({
                'mouseenter': this.mouseEnterHandler.bind(this),
                'mouseleave': this.mouseLeaveHandler.bind(this),
                'click': this.clickMenuHandler.bind(this),
                'keydown': this.keyDownMenuHandler.bind(this)
            });

            // Attach click and keydown event handlers to the individual speed
            // entries.
            this.speedsContainer.on({
                click: this.clickLinkHandler.bind(this),
                keydown: this.keyDownLinkHandler.bind(this)
            }, 'a.speed-link');

            this.state.el.on({
                'speed:set': function (event, speed) {
                    self.setSpeed(speed, true);
                },
                'speed:render': function (event, speeds, currentSpeed) {
                    self.render(speeds, currentSpeed);
                }
            });
        },

        /**
         * Check if playbackRate supports by browser. If browser supports, 1.0
         * should be returned by playbackRate property. In this case, function
         * return True. Otherwise, False will be returned.
         * iOS doesn't support speed change.
         * @param {object} state The object containing the state of the video
         * player.
         * @return {boolean}
         *   true: Browser support playbackRate functionality.
         *   false: Browser doesn't support playbackRate functionality.
         */
        isPlaybackRatesSupported: function (state) {
            var isHtml5 = state.videoType === 'html5',
                isTouch = state.isTouch,
                video = document.createElement('video');

            return !isTouch || (isHtml5 && !Boolean(video.playbackRate));
        },

        /**
         * Opens speed menu.
         * @param {boolean} [bindEvent] Click event will be attached on window.
         */
        openMenu: function (bindEvent) {
            // When speed entries have focus, the menu stays open on
            // mouseleave. A clickHandler is added to the window
            // element to have clicks close the menu when they happen
            // outside of it.
            if (bindEvent) {
                $(window).on('click.speedMenu', this.clickMenuHandler.bind(this));
            }

            this.el.addClass('is-opened');
            this.speedButton.attr('tabindex', -1);
        },

        /**
         * Closes speed menu.
         * @param {boolean} [unBindEvent] Click event will be detached from window.
         */
        closeMenu: function (unBindEvent) {
            // Remove the previously added clickHandler from window element.
            if (unBindEvent) {
                $(window).off('click.speedMenu');
            }

            this.el.removeClass('is-opened');
            this.speedButton.attr('tabindex', 0);
        },

        /**
         * Sets new current speed for the speed control and triggers `speedchange`
         * event if needed.
         * @param {string|number} speed Speed to be set.
         * @param {boolean} [silent] Sets the new speed without triggering
         * `speedchange` event.
         * @param {boolean} [forceUpdate] Updates the speed even if it's
         * not differs from current speed.
         */
        setSpeed: function (speed, silent, forceUpdate) {
            if (speed !== this.currentSpeed || forceUpdate) {
                this.speedsContainer
                    .find('li')
                    .removeClass('is-active')
                    .siblings("li[data-speed='" + speed + "']")
                    .addClass('is-active');

                this.speedButton.find('.value').html(speed + 'x');
                this.currentSpeed = speed;

                if (!silent) {
                    this.el.trigger('speedchange', [speed]);
                }
            }
        },

        /**
         * Click event handler for the menu.
         * @param {jquery Event} event
         */
        clickMenuHandler: function (event) {
            this.closeMenu();

            return false;
        },

        /**
         * Click event handler for speed links.
         * @param {jquery Event} event
         */
        clickLinkHandler: function (event) {
            var speed = $(event.currentTarget).parent().data('speed');

            this.closeMenu();
            this.state.videoCommands.execute('speed', speed);

            return false;
        },

        /**
         * Mouseenter event handler for the menu.
         * @param {jquery Event} event
         */
        mouseEnterHandler: function (event) {
            this.openMenu();

            return false;
        },

        /**
         * Mouseleave event handler for the menu.
         * @param {jquery Event} event
         */
        mouseLeaveHandler: function (event) {
            // Only close the menu is no speed entry has focus.
            if (!this.speedLinks.list.is(':focus')) {
                this.closeMenu();
            }
                    
            return false;
        },

        /**
         * Keydown event handler for the menu.
         * @param {jquery Event} event
         */
        keyDownMenuHandler: function (event) {
            var KEY = $.ui.keyCode,
                keyCode = event.keyCode;

            switch(keyCode) {
                // Open menu and focus on last element of list above it.
                case KEY.ENTER:
                case KEY.SPACE:
                case KEY.UP:
                    this.openMenu(true);
                    this.speedLinks.last().focus();
                    break;
                // Close menu.
                case KEY.ESCAPE:
                    this.closeMenu(true);
                    break;
            }
            // We do not stop propagation and default behavior on a TAB
            // keypress.
            return event.keyCode === KEY.TAB;
        },

        /**
         * Keydown event handler for speed links.
         * @param {jquery Event} event
         */
        keyDownLinkHandler: function (event) {
            // ALT key is used to change (alternate) the function of
            // other pressed keys. In this, do nothing.
            if (event.altKey) {
                return true;
            }

            var KEY = $.ui.keyCode,
                self = this,
                parent = $(event.currentTarget).parent(),
                index = parent.index(),
                speed = parent.data('speed');

            switch (event.keyCode) {
                // Close menu.
                case KEY.TAB:
                    // Closes menu after 25ms delay to change `tabindex` after
                    // finishing default behavior.
                    setTimeout(function () {
                        self.closeMenu(true);
                    }, 25);

                    return true;
                // Close menu and give focus to speed control.
                case KEY.ESCAPE:
                    this.closeMenu(true);
                    this.speedButton.focus();

                    return false;
                // Scroll up menu, wrapping at the top. Keep menu open.
                case KEY.UP:
                    // Shift + Arrows keyboard shortcut might be used by
                    // screen readers. In this, do nothing.
                    if (event.shiftKey) {
                        return true;
                    }

                    this.speedLinks.prev(index).focus();
                    return false;
                // Scroll down  menu, wrapping at the bottom. Keep menu
                // open.
                case KEY.DOWN:
                    // Shift + Arrows keyboard shortcut might be used by
                    // screen readers. In this, do nothing.
                    if (event.shiftKey) {
                        return true;
                    }

                    this.speedLinks.next(index).focus();
                    return false;
                // Close menu, give focus to speed control and change
                // speed.
                case KEY.ENTER:
                case KEY.SPACE:
                    this.closeMenu(true);
                    this.speedButton.focus();
                    this.setSpeed(this.state.speedToString(speed));

                    return false;
            }

            return true;
        }
    };

    return SpeedControl;
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
