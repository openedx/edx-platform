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
        var dfd = $.Deferred();

        state.videoCaption = {};

        _makeFunctionsPublic(state);

        state.videoCaption.renderElements();

        dfd.resolve();
        return dfd.promise();
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function _makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called,
    //     these functions will get the 'state' object as a context.
    function _makeFunctionsPublic(state) {
        var methodsDict = {
            addPaddings: addPaddings,
            bindHandlers: bindHandlers,
            bottomSpacingHeight: bottomSpacingHeight,
            calculateOffset: calculateOffset,
            captionBlur: captionBlur,
            captionClick: captionClick,
            captionFocus: captionFocus,
            captionHeight: captionHeight,
            captionKeyDown: captionKeyDown,
            captionMouseDown: captionMouseDown,
            captionMouseOverOut: captionMouseOverOut,
            fetchCaption: fetchCaption,
            fetchAvailableTranslations: fetchAvailableTranslations,
            hideCaptions: hideCaptions,
            onMouseEnter: onMouseEnter,
            onMouseLeave: onMouseLeave,
            onMovement: onMovement,
            pause: pause,
            play: play,
            renderCaption: renderCaption,
            renderElements: renderElements,
            renderLanguageMenu: renderLanguageMenu,
            reRenderCaption: reRenderCaption,
            resize: resize,
            scrollCaption: scrollCaption,
            search: search,
            seekPlayer: seekPlayer,
            setSubtitlesHeight: setSubtitlesHeight,
            toggle: toggle,
            topSpacingHeight: topSpacingHeight,
            updatePlayTime: updatePlayTime
        };

        state.bindTo(methodsDict, state.videoCaption, state);
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this'
    // keyword) is the 'state' object. The magic private function that makes
    // them available and sets up their context is makeFunctionsPublic().
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
        var Caption = this.videoCaption,
            languages = this.config.transcriptLanguages;

        Caption.loaded = false;
        Caption.subtitlesEl = this.el.find('ol.subtitles');
        Caption.container = this.el.find('.lang');
        Caption.hideSubtitlesEl = this.el.find('a.hide-subtitles');

        if (_.keys(languages).length) {
            Caption.renderLanguageMenu(languages);

            if (!Caption.fetchCaption()) {
                Caption.hideCaptions(true);
                Caption.hideSubtitlesEl.hide();
            }
        } else {
            Caption.hideCaptions(true, false);
            Caption.hideSubtitlesEl.hide();
        }
    }

    // function bindHandlers()
    //
    //     Bind any necessary function callbacks to DOM events (click,
    //     mousemove, etc.).
    function bindHandlers() {
        var self = this,
            Caption = this.videoCaption;

        $(window).bind('resize', Caption.resize);
        Caption.hideSubtitlesEl.on({
            'click': Caption.toggle
        });

        Caption.subtitlesEl.on({
            mouseenter: Caption.onMouseEnter,
            mouseleave: Caption.onMouseLeave,
            mousemove: Caption.onMovement,
            mousewheel: Caption.onMovement,
            DOMMouseScroll: Caption.onMovement
        });

        if (Caption.showLanguageMenu) {
            Caption.container.on({
                mouseenter: onContainerMouseEnter,
                mouseleave: onContainerMouseLeave
            });
        }

        this.el.on('speedchange', function () {
            if (self.currentPlayerMode === 'flash') {
                Caption.fetchCaption();
            }
        });

        if ((this.videoType === 'html5') && (this.config.autohideHtml5)) {
            Caption.subtitlesEl.on('scroll', this.videoControl.showControls);
        }
    }

    function onContainerMouseEnter(event) {
        event.preventDefault();

        $(event.currentTarget).addClass('open');
    }

    function onContainerMouseLeave(event) {
        event.preventDefault();

        $(event.currentTarget).removeClass('open');
    }

    function onMouseEnter() {
        if (this.videoCaption.frozen) {
            clearTimeout(this.videoCaption.frozen);
        }

        this.videoCaption.frozen = setTimeout(
            this.videoCaption.onMouseLeave,
            this.config.captionsFreezeTime
        );
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
        var self = this,
            Caption = self.videoCaption,
            data = {
                language: this.getCurrentLanguage()
            };

        if (Caption.loaded) {
            Caption.hideCaptions(false);
        } else {
            Caption.hideCaptions(this.hide_captions, false);
        }

        if (Caption.fetchXHR && Caption.fetchXHR.abort) {
            Caption.fetchXHR.abort();
        }

        if (this.videoType === 'youtube') {
            data.videoId = this.youtubeId();
        }

        // Fetch the captions file. If no file was specified, or if an error
        // occurred, then we hide the captions panel, and the "CC" button
        Caption.fetchXHR = $.ajaxWithPrefix({
            url: self.config.transcriptTranslationUrl,
            notifyOnError: false,
            data: data,
            success: function (captions) {
                Caption.captions = captions.text;
                Caption.start = captions.start;

                if (Caption.loaded) {
                    if (Caption.rendered) {
                        Caption.reRenderCaption();
                        Caption.updatePlayTime(self.videoPlayer.currentTime);
                    }
                } else {
                    if (self.isTouch) {
                        Caption.subtitlesEl.find('li').html(
                            gettext(
                                'Caption will be displayed when ' +
                                'you start playing the video.'
                            )
                        );
                    } else {
                        Caption.renderCaption();
                    }

                    Caption.bindHandlers();
                }

                Caption.loaded = true;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.log('[Video info]: ERROR while fetching captions.');
                console.log(
                    '[Video info]: STATUS:', textStatus +
                    ', MESSAGE:', '' + errorThrown
                );
                // If initial list of languages has more than 1 item, check
                // for availability other transcripts.
                if (_.keys(self.config.transcriptLanguages).length > 1) {
                    Caption.fetchAvailableTranslations();
                } else {
                    Caption.hideCaptions(true, false);
                    Caption.hideSubtitlesEl.hide();
                }
            }
        });

        return true;
    }

    function fetchAvailableTranslations() {
        var self = this,
            Caption = this.videoCaption;

        return $.ajaxWithPrefix({
            url: self.config.transcriptAvailableTranslationsUrl,
            notifyOnError: false,
            success: function (response) {
                var currentLanguages = self.config.transcriptLanguages,
                    newLanguages = _.pick(currentLanguages, response);

                // Update property with available currently translations.
                self.config.transcriptLanguages = newLanguages;
                // Remove an old language menu.
                Caption.container.find('.langs-list').remove();

                if (_.keys(newLanguages).length) {
                    // And try again to fetch transcript.
                    Caption.fetchCaption();
                    Caption.renderLanguageMenu(newLanguages);
                }
            },
            error: function (jqXHR, textStatus, errorThrown) {
                Caption.hideCaptions(true, false);
                Caption.hideSubtitlesEl.hide();
            }
        });
    }

    function resize() {
        this.videoCaption.subtitlesEl
            .find('.spacing:first')
            .height(this.videoCaption.topSpacingHeight())
            .find('.spacing:last')
            .height(this.videoCaption.bottomSpacingHeight());

        this.videoCaption.scrollCaption();

        this.videoCaption.setSubtitlesHeight();
    }

    function renderLanguageMenu(languages) {
        var self = this,
            menu = $('<ol class="langs-list menu">'),
            currentLang = this.getCurrentLanguage();

        if (_.keys(languages).length < 2) {
            return false;
        }

        this.videoCaption.showLanguageMenu = true;

        $.each(languages, function(code, label) {
            var li = $('<li data-lang-code="' + code + '" />'),
                link = $('<a href="javascript:void(0);">' + label + '</a>');

            if (currentLang === code) {
                li.addClass('active');
            }

            li.append(link);
            menu.append(li);
        });

        this.videoCaption.container.append(menu);

        menu.on('click', 'a', function (e) {
            var el = $(e.currentTarget).parent(),
                Caption = self.videoCaption,
                langCode = el.data('lang-code');

            if (self.lang !== langCode) {
                self.lang = langCode;
                self.storage.setItem('language', langCode);
                el  .addClass('active')
                    .siblings('li')
                    .removeClass('active');

                Caption.fetchCaption();
            }
        });
    }

    function buildCaptions (container, captions, start) {
        var fragment = document.createDocumentFragment();

        $.each(captions, function(index, text) {
            var liEl = $('<li>');

            liEl.html(text);

            liEl.attr({
                'data-index': index,
                'data-start': start[index],
                'tabindex': 0
            });

            fragment.appendChild(liEl[0]);
        });

        container.append([fragment]);
    }

    function renderCaption() {
        var Caption = this.videoCaption,
            events = ['mouseover', 'mouseout', 'mousedown', 'click', 'focus',
                'blur', 'keydown'].join(' ');

        Caption.setSubtitlesHeight();

        buildCaptions(Caption.subtitlesEl, Caption.captions, Caption.start);

        Caption.subtitlesEl.on(events, 'li[data-index]', function (event) {
            switch (event.type) {
                case 'mouseover':
                case 'mouseout':
                    Caption.captionMouseOverOut(event);
                    break;
                case 'mousedown':
                    Caption.captionMouseDown(event);
                    break;
                case 'click':
                    Caption.captionClick(event);
                    break;
                case 'focusin':
                    Caption.captionFocus(event);
                    break;
                case 'focusout':
                    Caption.captionBlur(event);
                    break;
                case 'keydown':
                    Caption.captionKeyDown(event);
                    break;
            }
        });

        // Enables or disables automatic scrolling of the captions when the
        // video is playing. This feature has to be disabled when tabbing
        // through them as it interferes with that action. Initially, have this
        // flag enabled as we assume mouse use. Then, if the first caption
        // (through forward tabbing) or the last caption (through backwards
        // tabbing) gets the focus, disable that feature. Re-enable it if tabbing
        // then cycles out of the the captions.
        Caption.autoScrolling = true;
        // Keeps track of where the focus is situated in the array of captions.
        // Used to implement the automatic scrolling behavior and decide if the
        // outline around a caption has to be hidden or shown on a mouseenter
        // or mouseleave. Initially, no caption has the focus, set the
        // index to -1.
        Caption.currentCaptionIndex = -1;
        // Used to track if the focus is coming from a click or tabbing. This
        // has to be known to decide if, when a caption gets the focus, an
        // outline has to be drawn (tabbing) or not (mouse click).
        Caption.isMouseFocus = false;
        Caption.addPaddings();
        Caption.rendered = true;
    }

    function reRenderCaption() {
        var Caption = this.videoCaption;

        Caption.currentIndex = null;
        Caption.rendered = false;
        Caption.subtitlesEl.empty();
        buildCaptions(Caption.subtitlesEl, Caption.captions, Caption.start);
        Caption.addPaddings();
        Caption.rendered = true;
    }

    function addPaddings() {
        // Set top and bottom spacing height and make sure they are taken out of
        // the tabbing order.
        this.videoCaption.subtitlesEl
            .prepend(
                $('<li class="spacing">')
                    .height(this.videoCaption.topSpacingHeight())
                    .attr('tabindex', -1)
            )
            .append(
                $('<li class="spacing">')
                    .height(this.videoCaption.bottomSpacingHeight())
                    .attr('tabindex', -1)
            );
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
            if (
                captionIndex <= 1 ||
                captionIndex >= this.videoCaption.captions.length - 2
            ) {
                this.videoCaption.autoScrolling = false;
            }
        }
    }

    function captionBlur(event) {
        var caption = $(event.target),
            captionIndex = parseInt(caption.attr('data-index'), 10);

        caption.removeClass('focused');
        // If we are on first or last index, we have to turn automatic scroll
        // on again when losing focus. There is no way to know in what
        // direction we are tabbing. So we could be on the first element and
        // tabbing back out of the captions or on the last element and tabbing
        // forward out of the captions.
        if (captionIndex === 0 ||
            captionIndex === this.videoCaption.captions.length - 1) {

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

        // Automatic scrolling gets disabled if one of the captions has
        // received focus through tabbing.
        if (
            !this.videoCaption.frozen &&
            el.length &&
            this.videoCaption.autoScrolling
        ) {
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
        return this.videoCaption.calculateOffset(
            this.videoCaption.subtitlesEl.find('li:not(.spacing):first')
        );
    }

    function bottomSpacingHeight() {
        return this.videoCaption.calculateOffset(
            this.videoCaption.subtitlesEl.find('li:not(.spacing):last')
        );
    }

    function toggle(event) {
        event.preventDefault();

        if (this.el.hasClass('closed')) {
            this.videoCaption.hideCaptions(false);
        } else {
            this.videoCaption.hideCaptions(true);
        }
    }

    function hideCaptions(hide_captions, update_cookie) {
        var hideSubtitlesEl = this.videoCaption.hideSubtitlesEl,
            type, text;

        if (typeof update_cookie === 'undefined') {
            update_cookie = true;
        }

        if (hide_captions) {
            type = 'hide_transcript';
            this.captionsHidden = true;

            this.el.addClass('closed');

            text = gettext('Turn on captions');
        } else {
            type = 'show_transcript';
            this.captionsHidden = false;

            this.el.removeClass('closed');
            this.videoCaption.scrollCaption();

            text = gettext('Turn off captions');
        }

        hideSubtitlesEl
            .attr('title', text)
            .text(gettext(text));

        if (this.videoPlayer) {
            this.videoPlayer.log(type, {
                currentTime: this.videoPlayer.currentTime
            });
        }

        if (this.resizer && !this.isFullScreen) {
            this.resizer.alignByWidthOnly();
        }

        this.videoCaption.setSubtitlesHeight();

        if (update_cookie) {
            $.cookie('hide_captions', hide_captions, {
                expires: 3650,
                path: '/'
            });
        }
    }

    function captionHeight() {
        var paddingTop;

        if (this.isFullScreen) {
            paddingTop = parseInt(
                this.videoCaption.subtitlesEl.css('padding-top'), 10
            );

            return $(window).height() -
                this.videoControl.el.height() -
                0.5 * this.videoControl.sliderEl.height() -
                2 * paddingTop;
        } else {
            return this.container.height();
        }
    }

    function setSubtitlesHeight() {
        var height = 0;
        // on page load captionHidden = undefined
        if  ((this.captionsHidden === undefined && this.hide_captions) ||
            this.captionsHidden === true
        ) {
            // In case of html5 autoshowing subtitles, we adjust height of
            // subs, by height of scrollbar.
            height = this.videoControl.el.height() +
                0.5 * this.videoControl.sliderEl.height();
            // Height of videoControl does not contain height of slider.
            // css is set to absolute, to avoid yanking when slider
            // autochanges its height.
        }

        this.videoCaption.subtitlesEl.css({
            maxHeight: this.videoCaption.captionHeight() - height
        });
    }
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
