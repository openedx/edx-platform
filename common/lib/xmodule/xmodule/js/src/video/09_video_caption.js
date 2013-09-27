(function (requirejs, require, define) {

// VideoCaption module.
define(
'video/09_video_caption.js',
[],
function () {

    /**
     * @desc VideoCaption module exports a function.
     *
     * @type {function}
     * @access public
     *
     * @param {object} state - The object containg the state of the video
     *     player. All other modules, their parameters, public variables, etc.
     *     are available via this object.
     *
     * @this {object} The global window object.
     *
     * @returns {undefined}
     */
    return function (state) {
        state.videoCaption = {};

        _makeFunctionsPublic(state);

        state.videoCaption.renderElements();
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function _makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function _makeFunctionsPublic(state) {
        state.videoCaption.autoShowCaptions        = _.bind(autoShowCaptions, state);
        state.videoCaption.autoHideCaptions        = _.bind(autoHideCaptions, state);
        state.videoCaption.resize                  = _.bind(resize, state);
        state.videoCaption.toggle                  = _.bind(toggle, state);
        state.videoCaption.onMouseEnter            = _.bind(onMouseEnter, state);
        state.videoCaption.onMouseLeave            = _.bind(onMouseLeave, state);
        state.videoCaption.onMovement              = _.bind(onMovement, state);
        state.videoCaption.renderCaption           = _.bind(renderCaption, state);
        state.videoCaption.captionHeight           = _.bind(captionHeight, state);
        state.videoCaption.topSpacingHeight        = _.bind(topSpacingHeight, state);
        state.videoCaption.bottomSpacingHeight     = _.bind(bottomSpacingHeight, state);
        state.videoCaption.scrollCaption           = _.bind(scrollCaption, state);
        state.videoCaption.search                  = _.bind(search, state);
        state.videoCaption.play                    = _.bind(play, state);
        state.videoCaption.pause                   = _.bind(pause, state);
        state.videoCaption.seekPlayer              = _.bind(seekPlayer, state);
        state.videoCaption.hideCaptions            = _.bind(hideCaptions, state);
        state.videoCaption.calculateOffset         = _.bind(calculateOffset, state);
        state.videoCaption.updatePlayTime          = _.bind(updatePlayTime, state);
        state.videoCaption.setSubtitlesHeight      = _.bind(setSubtitlesHeight, state);

        state.videoCaption.renderElements          = _.bind(renderElements, state);
        state.videoCaption.bindHandlers            = _.bind(bindHandlers, state);
        state.videoCaption.fetchCaption            = _.bind(fetchCaption, state);
        state.videoCaption.captionURL              = _.bind(captionURL, state);
        state.videoCaption.captionMouseOverOut     = _.bind(captionMouseOverOut, state);
        state.videoCaption.captionMouseDown        = _.bind(captionMouseDown, state);
        state.videoCaption.captionClick            = _.bind(captionClick, state);
        state.videoCaption.captionFocus            = _.bind(captionFocus, state);
        state.videoCaption.captionBlur             = _.bind(captionBlur, state);
        state.videoCaption.captionKeyDown          = _.bind(captionKeyDown, state);
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    /**
     * @desc Create any necessary DOM elements, attach them, and set their
     *     initial configuration. Also make the created DOM elements available
     *     via the 'state' object. Much easier to work this way - you don't
     *     have to do repeated jQuery element selects.
     *
     * @type {function}
     * @access public
     *
     * @this {object} - The object containg the state of the video
     *     player. All other modules, their parameters, public variables, etc.
     *     are available via this object.
     *
     * @returns {boolean}
     *     true: The function fethched captions successfully, and compltely
     *         rendered everything related to captions.
     *     false: The captions were not fetched. Nothing will be rendered,
     *         and the CC button will be hidden.
     */
    function renderElements() {
        this.videoCaption.loaded = false;

        this.videoCaption.subtitlesEl = this.el.find('ol.subtitles');
        this.videoCaption.hideSubtitlesEl = this.el.find('a.hide-subtitles');

        if (!this.videoCaption.fetchCaption()) {
            this.videoCaption.hideCaptions(true);
            this.videoCaption.hideSubtitlesEl.hide();
        }
        // ARIA
        // Let screen readers know this anchor behaves like a button.
        this.videoCaption.hideSubtitlesEl.attr('role', gettext('button'));
    }

    // function bindHandlers()
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function bindHandlers() {
        $(window).bind('resize', this.videoCaption.resize);
        this.videoCaption.hideSubtitlesEl.on('click', this.videoCaption.toggle);

        this.videoCaption.subtitlesEl
            .on(
                'mouseenter',
                this.videoCaption.onMouseEnter
            ).on(
                'mouseleave',
                this.videoCaption.onMouseLeave
            ).on(
                'mousemove',
                this.videoCaption.onMovement
            ).on(
                'mousewheel',
                this.videoCaption.onMovement
            ).on(
                'DOMMouseScroll',
                this.videoCaption.onMovement
            );

        if (this.videoType === 'html5') {
            this.el.on('mousemove', this.videoCaption.autoShowCaptions);
            this.el.on('keydown', this.videoCaption.autoShowCaptions);

            // Moving slider on subtitles is not a mouse move,
            // but captions and controls should be showed.
            this.videoCaption.subtitlesEl.on('scroll', this.videoCaption.autoShowCaptions);
            this.videoCaption.subtitlesEl.on('scroll', this.videoControl.showControls);
        }
    }

    /**
     * @desc Fetch the caption file specified by the user. Upn successful
     *     receival of the file, the captions will be rendered.
     *
     * @type {function}
     * @access public
     *
     * @this {object} - The object containg the state of the video
     *     player. All other modules, their parameters, public variables, etc.
     *     are available via this object.
     *
     * @returns {boolean}
     *     true: The user specified a caption file. NOTE: if an error happens
     *         while the specified file is being retrieved (for example the
     *         file is missing on the server), this function will still return
     *         true.
     *     false: No caption file was specified, or an empty string was
     *         specified.
     */
    function fetchCaption() {
        var _this = this;

        // Check whether the captions file was specified. This is the point
        // where we either stop with the caption panel (so that a white empty
        // panel to the right of the video will not be shown), or carry on
        // further.
        if (!this.youtubeId('1.0')) {
            return false;
        }

        // Fetch the captions file. If no file was specified, or if an error
        // occurred, then we hide the captions panel, and the "CC" button
        $.ajaxWithPrefix({
            url: _this.videoCaption.captionURL(),
            notifyOnError: false,
            success: function (captions) {
                _this.videoCaption.captions = captions.text;
                _this.videoCaption.start = captions.start;
                _this.videoCaption.loaded = true;

                if (onTouchBasedDevice()) {
                    _this.videoCaption.subtitlesEl.find('li').html(
                        gettext(
                            'Caption will be displayed when ' +
                            'you start playing the video.'
                        )
                    );
                } else {
                    _this.videoCaption.renderCaption();
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.log('ERROR while fetching captions.');
                console.log(
                    'STATUS:', textStatus + ', MESSAGE:', '' + errorThrown
                );

                _this.videoCaption.hideCaptions(true);
                _this.videoCaption.hideSubtitlesEl.hide();
            }
        });

        return true;
    }

    function captionURL() {
        return '' + this.config.caption_asset_path + this.youtubeId('1.0') + '.srt.sjson';
    }

    function autoShowCaptions(event) {
        if (!this.captionsShowLock) {
            if (!this.captionsHidden) {
                return;
            }

            this.captionsShowLock = true;

            if (this.captionState === 'invisible') {
                this.videoCaption.subtitlesEl.show();
                this.captionState = 'visible';
            } else if (this.captionState === 'hiding') {
                this.videoCaption.subtitlesEl.stop(true, false).css('opacity', 1).show();
                this.captionState = 'visible';
            } else if (this.captionState === 'visible') {
                clearTimeout(this.captionHideTimeout);
            }

            this.captionHideTimeout = setTimeout(this.videoCaption.autoHideCaptions, this.videoCaption.fadeOutTimeout);

            this.captionsShowLock = false;
        }
    }

    function autoHideCaptions() {
        var _this;

        this.captionHideTimeout = null;

        if (!this.captionsHidden) {
            return;
        }

        this.captionState = 'hiding';

        _this = this;

        this.videoCaption.subtitlesEl.fadeOut(this.videoCaption.fadeOutTimeout, function () {
            _this.captionState = 'invisible';
        });
    }

    function resize() {
        this.videoCaption.subtitlesEl
            .find('.spacing:first').height(this.videoCaption.topSpacingHeight())
            .find('.spacing:last').height(this.videoCaption.bottomSpacingHeight());

        this.videoCaption.scrollCaption();

        this.videoCaption.setSubtitlesHeight();
    }

    function onMouseEnter() {
        if (this.videoCaption.frozen) {
            clearTimeout(this.videoCaption.frozen);
        }

        this.videoCaption.frozen = setTimeout(this.videoCaption.onMouseLeave, 10000);
    }

    function onMouseLeave() {
        if (this.videoCaption.frozen) {
            clearTimeout(this.videoCaption.frozen);
        }

        this.videoCaption.frozen = null;

        if (this.videoCaption.playing) {
            this.videoCaption.scrollCaption();
        }
    }

    function onMovement() {
        this.videoCaption.onMouseEnter();
    }

    function renderCaption() {
        var container = $('<ol>'),
            _this = this;

        this.el.find('.video-wrapper').after(this.videoCaption.subtitlesEl);
        this.el.find('.video-controls .secondary-controls').append(this.videoCaption.hideSubtitlesEl);

        this.videoCaption.setSubtitlesHeight();

        if (this.videoType === 'html5') {
            this.videoCaption.fadeOutTimeout = this.config.fadeOutTimeout;

            this.videoCaption.subtitlesEl.addClass('html5');
            this.captionHideTimeout = setTimeout(this.videoCaption.autoHideCaptions, this.videoCaption.fadeOutTimeout);
        }

        this.videoCaption.hideCaptions(this.hide_captions);

        this.videoCaption.bindHandlers();

        $.each(this.videoCaption.captions, function(index, text) {
            var liEl = $('<li>');

            liEl.html(text);

            liEl.attr({
                'data-index': index,
                'data-start': _this.videoCaption.start[index],
                'tabindex': 0
            });

            container.append(liEl);
        });

        this.videoCaption.subtitlesEl.html(container.html());

        this.videoCaption.subtitlesEl.find('li[data-index]').on({
            mouseover:  this.videoCaption.captionMouseOverOut,
            mouseout:   this.videoCaption.captionMouseOverOut,
            mousedown:  this.videoCaption.captionMouseDown,
            click:      this.videoCaption.captionClick,
            focus:      this.videoCaption.captionFocus,
            blur:       this.videoCaption.captionBlur,
            keydown:    this.videoCaption.captionKeyDown
        });

        // Enables or disables automatic scrolling of the captions when the
        // video is playing. This feature has to be disabled when tabbing
        // through them as it interferes with that action. Initially, have this
        // flag enabled as we assume mouse use. Then, if the first caption 
        // (through forward tabbing) or the last caption (through backwards
        // tabbing) gets the focus, disable that feature. Renable it if tabbing
        // then cycles out of the the captions. 
        this.videoCaption.autoScrolling = true;
        // Keeps track of where the focus is situated in the array of captions.
        // Used to implement the automatic scrolling behavior and decide if the
        // outline around a caption has to be hidden or shown on a mouseenter or
        // mouseleave. Initially, no caption has the focus, set the index to -1.
        this.videoCaption.currentCaptionIndex = -1;
        // Used to track if the focus is coming from a click or tabbing. This 
        // has to be known to decide if, when a caption gets the focus, an 
        // outline has to be drawn (tabbing) or not (mouse click).
        this.videoCaption.isMouseFocus = false;

        this.videoCaption.subtitlesEl.prepend($('<li class="spacing">').height(this.videoCaption.topSpacingHeight()));
        this.videoCaption.subtitlesEl.append($('<li class="spacing">').height(this.videoCaption.bottomSpacingHeight()));

        this.videoCaption.rendered = true;
    }

    // On mouseOver, hide the outline of a caption that has been tabbed to.
    // On mouseOut, show the outline of a caption that has been tabbed to.
    function captionMouseOverOut(event) {
        var caption = $(event.target),
            captionIndex = parseInt(caption.attr('data-index'), 10); 
        if (captionIndex === this.videoCaption.currentCaptionIndex) {
            if (event.type === 'mouseover') {
                caption.removeClass('focused');
            }
            else { // mouseout
                caption.addClass('focused');
            }
        } 
    }

    function captionMouseDown(event) {
        var caption = $(event.target);
        this.videoCaption.isMouseFocus = true;
        this.videoCaption.autoScrolling = true;
        caption.removeClass('focused');
        this.videoCaption.currentCaptionIndex = -1;
    }

    function captionClick(event) {
        this.videoCaption.seekPlayer(event);
    }

    function captionFocus(event) {
        var caption = $(event.target),
            captionIndex = parseInt(caption.attr('data-index'), 10);
        // If the focus comes from a mouse click, hide the outline, turn on
        // automatic scrolling and set currentCaptionIndex to point outside of
        // caption list (ie -1) to disable mouseenter, mouseleave behavior. 
        if (this.videoCaption.isMouseFocus) {
            this.videoCaption.autoScrolling = true;
            caption.removeClass('focused');
            this.videoCaption.currentCaptionIndex = -1;
        }
        // If the focus comes from tabbing, show the outline and turn off 
        // automatic scrolling.
        else {
            this.videoCaption.currentCaptionIndex = captionIndex;
            caption.addClass('focused');
            // The second and second to last elements turn automatic scrolling
            // off again as it may have been enabled in captionBlur.    
            if (captionIndex <= 1 || captionIndex >= this.videoCaption.captions.length-2) {
                this.videoCaption.autoScrolling = false;
            }
        }
    }

    function captionBlur(event) {
        var caption = $(event.target), 
            captionIndex = parseInt(caption.attr('data-index'), 10);
        caption.removeClass('focused');
        // If we are on first or last index, we have to turn automatic scroll on
        // again when losing focus. There is no way to know in what direction we
        // are tabbing. So we could be on the first element and tabbing back out
        // of the captions or on the last element and tabbing forward out of the
        // captions.
        if (captionIndex === 0 || 
            captionIndex === this.videoCaption.captions.length-1) {
            this.videoCaption.autoScrolling = true;
        }
    }

    function captionKeyDown(event) {
        this.videoCaption.isMouseFocus = false;
        if (event.which === 13) { //Enter key
            this.videoCaption.seekPlayer(event);
        }
    }

    function scrollCaption() {
        var el = this.videoCaption.subtitlesEl.find('.current:first');

        // Automatic scrolling gets disabled if one of the captions has received 
        // focus through tabbing. 
        if (!this.videoCaption.frozen && el.length && this.videoCaption.autoScrolling) {
            this.videoCaption.subtitlesEl.scrollTo(
                el,
                {
                    offset: -this.videoCaption.calculateOffset(el)
                }
            );
        }
    }

    function search(time) {
        var index, max, min;

        if (this.videoCaption.loaded) {
            min = 0;
            max = this.videoCaption.start.length - 1;

            if (time < this.videoCaption.start[min]) {
                return -1;
            }
            while (min < max) {
                index = Math.ceil((max + min) / 2);

                if (time < this.videoCaption.start[index]) {
                    max = index - 1;
                }

                if (time >= this.videoCaption.start[index]) {
                    min = index;
                }
            }

            return min;
        }

        return undefined;
    }

    function play() {
        if (this.videoCaption.loaded) {
            if (!this.videoCaption.rendered) {
                this.videoCaption.renderCaption();
            }

            this.videoCaption.playing = true;
        }
    }

    function pause() {
        if (this.videoCaption.loaded) {
            this.videoCaption.playing = false;
        }
    }

    function updatePlayTime(time) {
        var newIndex;

        if (this.videoCaption.loaded) {
            // Current mode === 'flash' can only be for YouTube videos. So, we
            // don't have to also check for videoType === 'youtube'.
            if (this.currentPlayerMode === 'flash') {
                // Total play time changes with speed change. Also there is
                // a 250 ms delay we have to take into account.
                time = Math.round(
                    Time.convert(time, this.speed, '1.0') * 1000 + 100
                );
            } else {
                // Total play time remains constant when speed changes.
                time = Math.round(time * 1000 + 100);
            }

            newIndex = this.videoCaption.search(time);

            if (
                typeof newIndex !== 'undefined' &&
                newIndex !== -1 &&
                this.videoCaption.currentIndex !== newIndex
            ) {
                if (typeof this.videoCaption.currentIndex !== 'undefined') {
                    this.videoCaption.subtitlesEl
                        .find('li.current')
                        .removeClass('current');
                }

                this.videoCaption.subtitlesEl
                    .find("li[data-index='" + newIndex + "']")
                    .addClass('current');

                this.videoCaption.currentIndex = newIndex;

                this.videoCaption.scrollCaption();
            }
        }
    }

    function seekPlayer(event) {
        var time;

        event.preventDefault();

        // Current mode === 'flash' can only be for YouTube videos. So, we
        // don't have to also check for videoType === 'youtube'.
        if (this.currentPlayerMode === 'flash') {
            // Total play time changes with speed change. Also there is
            // a 250 ms delay we have to take into account.
            time = Math.round(
                Time.convert(
                    $(event.target).data('start'), '1.0', this.speed
                ) / 1000
            );
        } else {
            // Total play time remains constant when speed changes.
            time = parseInt($(event.target).data('start'), 10)/1000;
        }

        this.trigger(
            'videoPlayer.onCaptionSeek',
            {
                'type': 'onCaptionSeek',
                'time': time
            }
        );
    }

    function calculateOffset(element) {
        return this.videoCaption.captionHeight() / 2 - element.height() / 2;
    }

    function topSpacingHeight() {
        return this.videoCaption.calculateOffset(this.videoCaption.subtitlesEl.find('li:not(.spacing):first'));
    }

    function bottomSpacingHeight() {
        return this.videoCaption.calculateOffset(this.videoCaption.subtitlesEl.find('li:not(.spacing):last'));
    }

    function toggle(event) {
        event.preventDefault();

        if (this.el.hasClass('closed')) {
            this.videoCaption.hideCaptions(false);
        } else {
            this.videoCaption.hideCaptions(true);
        }
    }

    function hideCaptions(hide_captions) {
        var type;

        if (hide_captions) {
            type = 'hide_transcript';
            this.captionsHidden = true;
            this.videoCaption.hideSubtitlesEl.attr('title', gettext('Turn on captions'));
            this.el.addClass('closed');
        } else {
            type = 'show_transcript';
            this.captionsHidden = false;
            this.videoCaption.hideSubtitlesEl.attr('title', gettext('Turn off captions'));
            this.el.removeClass('closed');
            this.videoCaption.scrollCaption();
        }

        if (this.videoPlayer) {
            this.videoPlayer.log(type, {
                currentTime: this.videoPlayer.currentTime
            });
        }

        this.videoCaption.setSubtitlesHeight();

        $.cookie('hide_captions', hide_captions, {
            expires: 3650,
            path: '/'
        });
    }

    function captionHeight() {
        if (this.isFullScreen) {
            return $(window).height() - this.el.find('.video-controls').height() -
                    0.5 * this.videoControl.sliderEl.height() -
                    2 * parseInt(this.videoCaption.subtitlesEl.css('padding-top'), 10);
        } else {
            return this.el.find('.video-wrapper').height();
        }
    }

    function setSubtitlesHeight() {
        var height = 0;
        if (this.videoType === 'html5'){
            // on page load captionHidden = undefined
            if  (
                (this.captionsHidden === undefined && this.hide_captions === true ) ||
                (this.captionsHidden === true) ) {
                // In case of html5 autoshowing subtitles,
                // we ajdust height of subs, by height of scrollbar
                height = this.videoControl.el.height() + 0.5 * this.videoControl.sliderEl.height();
                // height of videoControl does not contain height of slider.
                // (css is set to absolute, to avoid yanking when slider autochanges its height)
            }
        }
        this.videoCaption.subtitlesEl.css({
            maxHeight: this.videoCaption.captionHeight() - height
        });
     }
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
