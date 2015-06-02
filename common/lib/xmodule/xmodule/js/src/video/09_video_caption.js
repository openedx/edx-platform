(function (define) {

// VideoCaption module.
define(
'video/09_video_caption.js',
['video/00_sjson.js', 'video/00_async_process.js'],
function (Sjson, AsyncProcess) {
    /**
     * @desc VideoCaption module exports a function.
     *
     * @type {function}
     * @access public
     *
     * @param {object} state - The object containing the state of the video
     *     player. All other modules, their parameters, public variables, etc.
     *     are available via this object.
     *
     * @this {object} The global window object.
     *
     * @returns {jquery Promise}
     */
    var VideoCaption = function (state) {
        if (!(this instanceof VideoCaption)) {
            return new VideoCaption(state);
        }

        this.state = state;
        this.state.videoCaption = this;
        this.renderElements();

        return $.Deferred().resolve().promise();
    };

    VideoCaption.prototype = {
        /**
        * @desc Initiate rendering of elements, and set their initial configuration.
        *
        */
        renderElements: function () {
            var state = this.state,
                languages = this.state.config.transcriptLanguages;

            this.loaded = false;
            this.subtitlesEl = state.el.find('ol.subtitles');
            this.container = state.el.find('.lang');
            this.hideSubtitlesEl = state.el.find('a.hide-subtitles');

            if (_.keys(languages).length) {
                this.renderLanguageMenu(languages);

                if (!this.fetchCaption()) {
                    this.hideCaptions(true);
                    this.hideSubtitlesEl.hide();
                }
            } else {
                this.hideCaptions(true, false);
                this.hideSubtitlesEl.hide();
            }
        },

        /**
        * @desc Bind any necessary function callbacks to DOM events (click,
        *     mousemove, etc.).
        *
        */
        bindHandlers: function () {
            var self = this,
                state = this.state,
                events = [
                    'mouseover', 'mouseout', 'mousedown', 'click', 'focus', 'blur',
                    'keydown'
                ].join(' ');

            // Change context to VideoCaption of event handlers using `bind`.
            this.hideSubtitlesEl.on('click', this.toggle.bind(this));
            this.subtitlesEl
                .on({
                    mouseenter: this.onMouseEnter.bind(this),
                    mouseleave: this.onMouseLeave.bind(this),
                    mousemove: this.onMovement.bind(this),
                    mousewheel: this.onMovement.bind(this),
                    DOMMouseScroll: this.onMovement.bind(this)
                })
                .on(events, 'li[data-index]', function (event) {
                    switch (event.type) {
                        case 'mouseover':
                        case 'mouseout':
                            self.captionMouseOverOut(event);
                            break;
                        case 'mousedown':
                            self.captionMouseDown(event);
                            break;
                        case 'click':
                            self.captionClick(event);
                            break;
                        case 'focusin':
                            self.captionFocus(event);
                            break;
                        case 'focusout':
                            self.captionBlur(event);
                            break;
                        case 'keydown':
                            self.captionKeyDown(event);
                            break;
                    }
                });

            if (this.showLanguageMenu) {
                this.container.on({
                    mouseenter: this.onContainerMouseEnter.bind(this),
                    mouseleave: this.onContainerMouseLeave.bind(this)
                });
            }

            state.el
                .on({
                    'caption:fetch': this.fetchCaption.bind(this),
                    'caption:resize': this.onResize.bind(this),
                    'caption:update': function (event, time) {
                        self.updatePlayTime(time);
                    },
                    'ended': this.pause.bind(this),
                    'fullscreen': this.onResize.bind(this),
                    'pause': this.pause.bind(this),
                    'play': this.play.bind(this)
                });

            if ((state.videoType === 'html5') && (state.config.autohideHtml5)) {
                this.subtitlesEl.on('scroll', state.videoControl.showControls);
            }
        },


        /**
        * @desc Opens language menu.
        *
        * @param {jquery Event} event
        */
        onContainerMouseEnter: function (event) {
            event.preventDefault();
            this.state.videoPlayer.log('video_show_cc_menu', {});
            $(event.currentTarget).addClass('is-opened');
        },

        /**
        * @desc Closes language menu.
        *
        * @param {jquery Event} event
        */
        onContainerMouseLeave: function (event) {
            event.preventDefault();
            this.state.videoPlayer.log('video_hide_cc_menu', {});
            $(event.currentTarget).removeClass('is-opened');
        },

        /**
        * @desc Freezes moving of captions when mouse is over them.
        *
        * @param {jquery Event} event
        */
        onMouseEnter: function (event) {
            if (this.frozen) {
                clearTimeout(this.frozen);
            }

            this.frozen = setTimeout(
                this.onMouseLeave,
                this.state.config.captionsFreezeTime
            );
        },

        /**
        * @desc Unfreezes moving of captions when mouse go out.
        *
        * @param {jquery Event} event
        */
        onMouseLeave: function (event) {
            if (this.frozen) {
                clearTimeout(this.frozen);
            }

            this.frozen = null;

            if (this.playing) {
                this.scrollCaption();
            }
        },

        /**
        * @desc Freezes moving of captions when mouse is moving over them.
        *
        * @param {jquery Event} event
        */
        onMovement: function (event) {
            this.onMouseEnter();
        },

        /**
         * @desc Gets the correct start and end times from the state configuration
         *
         * @returns {array} if [startTime, endTime] are defined
         */
        getStartEndTimes: function () {
            // due to the way config.startTime/endTime are
            // processed in 03_video_player.js, we assume
            // endTime can be an integer or null,
            // and startTime is an integer > 0
            var config = this.state.config;
            var startTime = config.startTime * 1000;
            var endTime = (config.endTime !== null) ? config.endTime * 1000 : null;
            return [startTime, endTime];
        },

        /**
         * @desc Gets captions within the start / end times stored within this.state.config
         *
         * @returns {object} {start, captions} parallel arrays of
         *    start times and corresponding captions
         */
        getBoundedCaptions: function () {
            // get start and caption. If startTime and endTime
            // are specified, filter by that range.
            var times = this.getStartEndTimes();
            var results = this.sjson.filter.apply(this.sjson, times);
            var start = results.start;
            var captions = results.captions;

            return {
              'start': start,
              'captions': captions
            };
        },

        /**
        * @desc Fetch the caption file specified by the user. Upon successful
        *     receipt of the file, the captions will be rendered.
        *
        * @returns {boolean}
        *     true: The user specified a caption file. NOTE: if an error happens
        *         while the specified file is being retrieved (for example the
        *         file is missing on the server), this function will still return
        *         true.
        *     false: No caption file was specified, or an empty string was
        *         specified for the Youtube type player.
        */
        fetchCaption: function () {
            var self = this,
                state = this.state,
                language = state.getCurrentLanguage(),
                data, youtubeId;

            if (this.loaded) {
                this.hideCaptions(false);
            } else {
                this.hideCaptions(state.hide_captions, false);
            }

            if (this.fetchXHR && this.fetchXHR.abort) {
                this.fetchXHR.abort();
            }

            if (state.videoType === 'youtube') {
                youtubeId = state.youtubeId('1.0');

                if (!youtubeId) {
                    return false;
                }

                data = {
                    videoId: youtubeId
                };
            }

            state.el.removeClass('is-captions-rendered');
            // Fetch the captions file. If no file was specified, or if an error
            // occurred, then we hide the captions panel, and the "CC" button
            this.fetchXHR = $.ajaxWithPrefix({
                url: state.config.transcriptTranslationUrl + '/' + language,
                notifyOnError: false,
                data: data,
                success: function (sjson) {
                    self.sjson = new Sjson(sjson);
                    var results = self.getBoundedCaptions();
                    var start = results.start;
                    var captions = results.captions;

                    if (self.loaded) {
                        if (self.rendered) {
                            self.renderCaption(start, captions);
                            self.updatePlayTime(state.videoPlayer.currentTime);
                        }
                    } else {
                        if (state.isTouch) {
                            self.subtitlesEl.find('li').html(
                                gettext(
                                    'Caption will be displayed when ' +
                                    'you start playing the video.'
                                )
                            );
                        } else {
                            self.renderCaption(start, captions);
                        }

                        self.bindHandlers();
                    }

                    self.loaded = true;
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    console.log('[Video info]: ERROR while fetching captions.');
                    console.log(
                        '[Video info]: STATUS:', textStatus +
                        ', MESSAGE:', '' + errorThrown
                    );
                    // If initial list of languages has more than 1 item, check
                    // for availability other transcripts.
                    if (_.keys(state.config.transcriptLanguages).length > 1) {
                        self.fetchAvailableTranslations();
                    } else {
                        self.hideCaptions(true, false);
                        self.hideSubtitlesEl.hide();
                    }
                }
            });

            return true;
        },

        /**
        * @desc Fetch the list of available translations. Upon successful receipt,
        *    the list of available translations will be updated.
        *
        * @returns {jquery Promise}
        */
        fetchAvailableTranslations: function () {
            var self = this,
                state = this.state;

            return $.ajaxWithPrefix({
                url: state.config.transcriptAvailableTranslationsUrl,
                notifyOnError: false,
                success: function (response) {
                    var currentLanguages = state.config.transcriptLanguages,
                        newLanguages = _.pick(currentLanguages, response);

                    // Update property with available currently translations.
                    state.config.transcriptLanguages = newLanguages;
                    // Remove an old language menu.
                    self.container.find('.langs-list').remove();

                    if (_.keys(newLanguages).length) {
                        // And try again to fetch transcript.
                        self.fetchCaption();
                        self.renderLanguageMenu(newLanguages);
                    }
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    self.hideCaptions(true, false);
                    self.hideSubtitlesEl.hide();
                }
            });
        },

        /**
        * @desc Recalculates and updates the height of the container of captions.
        *
        */
        onResize: function () {
            this.subtitlesEl
                .find('.spacing').first()
                .height(this.topSpacingHeight()).end()
                .find('.spacing').last()
                .height(this.bottomSpacingHeight());

            this.scrollCaption();
            this.setSubtitlesHeight();
        },

        /**
        * @desc Create any necessary DOM elements, attach them, and set their
        *     initial configuration for the Language menu.
        *
        * @param {object} languages Dictionary where key is language code,
        *     value - language label
        *
        */
        renderLanguageMenu: function (languages) {
            var self = this,
                state = this.state,
                menu = $('<ol class="langs-list menu">'),
                currentLang = state.getCurrentLanguage();

            if (_.keys(languages).length < 2) {
                return false;
            }

            this.showLanguageMenu = true;

            $.each(languages, function(code, label) {
                var li = $('<li data-lang-code="' + code + '" />'),
                    link = $('<a href="javascript:void(0);">' + label + '</a>');

                if (currentLang === code) {
                    li.addClass('is-active');
                }

                li.append(link);
                menu.append(li);
            });

            this.container.append(menu);

            menu.on('click', 'a', function (e) {
                var el = $(e.currentTarget).parent(),
                    state = self.state,
                    langCode = el.data('lang-code');

                if (state.lang !== langCode) {
                    state.lang = langCode;
                    state.storage.setItem('language', langCode);
                    el  .addClass('is-active')
                        .siblings('li')
                        .removeClass('is-active');

                    self.fetchCaption();
                }
            });
        },

        /**
        * @desc Create any necessary DOM elements, attach them, and set their
        *     initial configuration.
        *
        * @param {jQuery element} container Element in which captions will be
        *     inserted.
        * @param {array} start List of start times for the video.
        * @param {array} captions List of captions for the video.
        * @returns {object} jQuery's Promise object
        *
        */
        buildCaptions: function  (container, start, captions) {
            var process = function(text, index) {
                    var liEl = $('<li>', {
                        'data-index': index,
                        'data-start': start[index],
                        'tabindex': 0
                    }).html(text);

                    return liEl[0];
                };

            return AsyncProcess.array(captions, process).done(function (list) {
                container.append(list);
            });
        },

        /**
        * @desc Initiates creating of captions and set their initial configuration.
        *
        * @param {array} start List of start times for the video.
        * @param {array} captions List of captions for the video.
        *
        */
        renderCaption: function (start, captions) {
            var self = this;

            var onRender = function () {
                self.addPaddings();
                // Enables or disables automatic scrolling of the captions when the
                // video is playing. This feature has to be disabled when tabbing
                // through them as it interferes with that action. Initially, have
                // this flag enabled as we assume mouse use. Then, if the first
                // caption (through forward tabbing) or the last caption (through
                // backwards tabbing) gets the focus, disable that feature.
                // Re-enable it if tabbing then cycles out of the the captions.
                self.autoScrolling = true;
                // Keeps track of where the focus is situated in the array of
                // captions. Used to implement the automatic scrolling behavior and
                // decide if the outline around a caption has to be hidden or shown
                // on a mouseenter or mouseleave. Initially, no caption has the
                // focus, set the index to -1.
                self.currentCaptionIndex = -1;
                // Used to track if the focus is coming from a click or tabbing. This
                // has to be known to decide if, when a caption gets the focus, an
                // outline has to be drawn (tabbing) or not (mouse click).
                self.isMouseFocus = false;
                self.rendered = true;
                self.state.el.addClass('is-captions-rendered');
            };

            this.rendered = false;
            this.subtitlesEl.empty();
            this.setSubtitlesHeight();
            this.buildCaptions(this.subtitlesEl, start, captions).done(onRender);
        },

        /**
        * @desc Sets top and bottom spacing height and make sure they are taken
        *     out of the tabbing order.
        *
        */
        addPaddings: function () {

            this.subtitlesEl
                .prepend(
                    $('<li class="spacing">')
                        .height(this.topSpacingHeight())
                        .attr('tabindex', -1)
                )
                .append(
                    $('<li class="spacing">')
                        .height(this.bottomSpacingHeight())
                        .attr('tabindex', -1)
                );
        },

        /**
        * @desc
        * On mouseOver: Hides the outline of a caption that has been tabbed to.
        * On mouseOut: Shows the outline of a caption that has been tabbed to.
        *
        * @param {jquery Event} event
        *
        */
        captionMouseOverOut: function (event) {
            var caption = $(event.target),
                captionIndex = parseInt(caption.attr('data-index'), 10);

            if (captionIndex === this.currentCaptionIndex) {
                if (event.type === 'mouseover') {
                    caption.removeClass('focused');
                }
                else { // mouseout
                    caption.addClass('focused');
                }
            }
        },

        /**
        * @desc Handles mousedown event on concrete caption.
        *
        * @param {jquery Event} event
        *
        */
        captionMouseDown: function (event) {
            var caption = $(event.target);

            this.isMouseFocus = true;
            this.autoScrolling = true;
            caption.removeClass('focused');
            this.currentCaptionIndex = -1;
        },

        /**
        * @desc Handles click event on concrete caption.
        *
        * @param {jquery Event} event
        *
        */
        captionClick: function (event) {
            this.seekPlayer(event);
        },

        /**
        * @desc Handles focus event on concrete caption.
        *
        * @param {jquery Event} event
        *
        */
        captionFocus: function (event) {
            var caption = $(event.target),
                captionIndex = parseInt(caption.attr('data-index'), 10);
            // If the focus comes from a mouse click, hide the outline, turn on
            // automatic scrolling and set currentCaptionIndex to point outside of
            // caption list (ie -1) to disable mouseenter, mouseleave behavior.
            if (this.isMouseFocus) {
                this.autoScrolling = true;
                caption.removeClass('focused');
                this.currentCaptionIndex = -1;
            }
            // If the focus comes from tabbing, show the outline and turn off
            // automatic scrolling.
            else {
                this.currentCaptionIndex = captionIndex;
                caption.addClass('focused');
                // The second and second to last elements turn automatic scrolling
                // off again as it may have been enabled in captionBlur.
                if (
                    captionIndex <= 1 ||
                    captionIndex >= this.sjson.getSize() - 2
                ) {
                    this.autoScrolling = false;
                }
            }
        },

        /**
        * @desc Handles blur event on concrete caption.
        *
        * @param {jquery Event} event
        *
        */
        captionBlur: function (event) {
            var caption = $(event.target),
                captionIndex = parseInt(caption.attr('data-index'), 10);

            caption.removeClass('focused');
            // If we are on first or last index, we have to turn automatic scroll
            // on again when losing focus. There is no way to know in what
            // direction we are tabbing. So we could be on the first element and
            // tabbing back out of the captions or on the last element and tabbing
            // forward out of the captions.
            if (captionIndex === 0 ||
                captionIndex === this.sjson.getSize() - 1) {

                this.autoScrolling = true;
            }
        },

        /**
        * @desc Handles keydown event on concrete caption.
        *
        * @param {jquery Event} event
        *
        */
        captionKeyDown: function (event) {
            this.isMouseFocus = false;
            if (event.which === 13) { //Enter key
                this.seekPlayer(event);
            }
        },

        /**
        * @desc Scrolls caption container to make active caption visible.
        *
        */
        scrollCaption: function () {
            var el = this.subtitlesEl.find('.current:first');

            // Automatic scrolling gets disabled if one of the captions has
            // received focus through tabbing.
            if (
                !this.frozen &&
                el.length &&
                this.autoScrolling
            ) {
                this.subtitlesEl.scrollTo(
                    el,
                    {
                        offset: -1 * this.calculateOffset(el)
                    }
                );
            }
        },

        /**
        * @desc Updates flags on play
        *
        */
        play: function () {
            var startAndCaptions, start, end;
            if (this.loaded) {
                if (!this.rendered) {
                    startAndCaptions = this.getBoundedCaptions();
                    start = startAndCaptions.start;
                    captions = startAndCaptions.captions;
                    this.renderCaption(start, captions);
                }

                this.playing = true;
            }
        },

        /**
        * @desc Updates flags on pause
        *
        */
        pause: function () {
            if (this.loaded) {
                this.playing = false;
            }
        },

        /**
        * @desc Updates captions UI on paying.
        *
        * @param {number} time Time in seconds.
        *
        */
        updatePlayTime: function (time) {
            var state = this.state,
                startTime,
                endTime,
                params,
                newIndex;

            if (this.loaded) {
                if (state.isFlashMode()) {
                    time = Time.convert(time, state.speed, '1.0');
                }

                time = Math.round(time * 1000 + 100);
                var times = this.getStartEndTimes();
                // if start and end times are defined, limit search.
                // else, use the entire list of video captions
                params = [time].concat(times);
                newIndex = this.sjson.search.apply(this.sjson, params);

                if (
                    typeof newIndex !== 'undefined' &&
                    newIndex !== -1 &&
                    this.currentIndex !== newIndex
                ) {
                    if (typeof this.currentIndex !== 'undefined') {
                        this.subtitlesEl
                            .find('li.current')
                            .removeClass('current');
                    }

                    this.subtitlesEl
                        .find("li[data-index='" + newIndex + "']")
                        .addClass('current');

                    this.currentIndex = newIndex;
                    this.scrollCaption();
                }
            }
        },

        /**
        * @desc Sends log to the server on caption seek.
        *
        * @param {jquery Event} event
        *
        */
        seekPlayer: function (event) {
            var state = this.state,
                time = parseInt($(event.target).data('start'), 10);

            if (state.isFlashMode()) {
                time = Math.round(Time.convert(time, '1.0', state.speed));
            }

            state.trigger(
                'videoPlayer.onCaptionSeek',
                {
                    'type': 'onCaptionSeek',
                    'time': time/1000
                }
            );

            event.preventDefault();
        },

        /**
        * @desc Calculates offset for paddings.
        *
        * @param {jquery element} element Top or bottom padding element.
        * @returns {number} Offset for the passed padding element.
        *
        */
        calculateOffset: function (element) {
            return this.captionHeight() / 2 - element.height() / 2;
        },

        /**
        * @desc Calculates offset for the top padding element.
        *
        * @returns {number} Offset for the passed top padding element.
        *
        */
        topSpacingHeight: function () {
            return this.calculateOffset(
                this.subtitlesEl.find('li:not(.spacing)').first()
            );
        },

        /**
        * @desc Calculates offset for the bottom padding element.
        *
        * @returns {number} Offset for the passed bottom padding element.
        *
        */
        bottomSpacingHeight: function () {
            return this.calculateOffset(
                this.subtitlesEl.find('li:not(.spacing)').last()
            );
        },

        /**
        * @desc Shows/Hides captions on click `CC` button
        *
        * @param {jquery Event} event
        *
        */
        toggle: function (event) {
            event.preventDefault();

            if (this.state.el.hasClass('closed')) {
                this.hideCaptions(false);
            } else {
                this.hideCaptions(true);
            }
        },

        /**
        * @desc Shows/Hides captions and updates the cookie.
        *
        * @param {boolean} hide_captions if `true` hides the caption,
        *     otherwise - show.
        * @param {boolean} update_cookie Flag to update or not the cookie.
        *
        */
        hideCaptions: function (hide_captions, update_cookie) {
            var hideSubtitlesEl = this.hideSubtitlesEl,
                state = this.state,
                type, text;

            if (typeof update_cookie === 'undefined') {
                update_cookie = true;
            }

            if (hide_captions) {
                type = 'hide_transcript';
                state.captionsHidden = true;
                state.el.addClass('closed');
                text = gettext('Turn on captions');
            } else {
                type = 'show_transcript';
                state.captionsHidden = false;
                state.el.removeClass('closed');
                this.scrollCaption();
                text = gettext('Turn off captions');
            }

            hideSubtitlesEl
                .attr('title', text)
                .text(gettext(text));

            if (state.videoPlayer) {
                state.videoPlayer.log(type, {
                    currentTime: state.videoPlayer.currentTime
                });
            }

            if (state.resizer) {
                if (state.isFullScreen) {
                    state.resizer.setMode('both');
                } else {
                    state.resizer.alignByWidthOnly();
                }
            }

            this.setSubtitlesHeight();
            if (update_cookie) {
                $.cookie('hide_captions', hide_captions, {
                    expires: 3650,
                    path: '/'
                });
            }
        },

        /**
        * @desc Return the caption container height.
        *
        * @returns {number} event Height of the container in pixels.
        *
        */
        captionHeight: function () {
            var state = this.state;

            if (state.isFullScreen) {
                return state.container.height() - state.videoControl.height;
            } else {
                return state.container.height();
            }
        },

        /**
        * @desc Sets the height of the caption container element.
        *
        */
        setSubtitlesHeight: function () {
            var height = 0,
                state = this.state;
            // on page load captionHidden = undefined
            if  ((state.captionsHidden === undefined && state.hide_captions) ||
                state.captionsHidden === true
            ) {
                // In case of html5 autoshowing subtitles, we adjust height of
                // subs, by height of scrollbar.
                height = state.videoControl.el.height() +
                    0.5 * state.videoControl.sliderEl.height();
                // Height of videoControl does not contain height of slider.
                // css is set to absolute, to avoid yanking when slider
                // autochanges its height.
            }

            this.subtitlesEl.css({
                maxHeight: this.captionHeight() - height
            });
        }
    };

    return VideoCaption;
});

}(RequireJS.define));
