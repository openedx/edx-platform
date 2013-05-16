(function (requirejs, require, define) {

// VideoCaption module.
define(
'videoalpha/display/video_caption.js',
[],
function () {

    // VideoCaption() function - what this module "exports".
    return function (state) {
        state.videoCaption = {};

        makeFunctionsPublic(state);
        renderElements(state);
        bindHandlers(state);
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function makeFunctionsPublic(state) {
        state.videoCaption.autoShowCaptions    = autoShowCaptions.bind(state);
        state.videoCaption.autoHideCaptions    = autoHideCaptions.bind(state);
        state.videoCaption.resize              = resize.bind(state);
        state.videoCaption.toggle              = toggle.bind(state);
        state.videoCaption.onMouseEnter        = onMouseEnter.bind(state);
        state.videoCaption.onMouseLeave        = onMouseLeave.bind(state);
        state.videoCaption.onMovement          = onMovement.bind(state);
        state.videoCaption.renderCaption       = renderCaption.bind(state);
        state.videoCaption.captionHeight       = captionHeight.bind(state);
        state.videoCaption.topSpacingHeight    = topSpacingHeight.bind(state);
        state.videoCaption.bottomSpacingHeight = bottomSpacingHeight.bind(state);
        state.videoCaption.scrollCaption       = scrollCaption.bind(state);
        state.videoCaption.search              = search.bind(state);
        state.videoCaption.play                = play.bind(state);
        state.videoCaption.pause               = pause.bind(state);
        state.videoCaption.seekPlayer          = seekPlayer.bind(state);
        state.videoCaption.hideCaptions        = hideCaptions.bind(state);
        state.videoCaption.calculateOffset     = calculateOffset.bind(state);
        state.videoCaption.updatePlayTime      = updatePlayTime.bind(state);
    }

    // function renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function renderElements(state) {
        state.videoCaption.loaded = false;

        state.videoCaption.subtitlesEl = state.el.find('ol.subtitles');
        state.videoCaption.hideSubtitlesEl = state.el.find('a.hide-subtitles');

        state.el.find('.video-wrapper').after(state.videoCaption.subtitlesEl);
        state.el.find('.video-controls .secondary-controls').append(state.videoCaption.hideSubtitlesEl);

        state.el.find('.subtitles').css({
            maxHeight: state.el.find('.video-wrapper').height() - 5
        });

        fetchCaption(state);

        if (state.videoType === 'html5') {
            state.videoCaption.fadeOutTimeout = state.config.fadeOutTimeout;

            state.videoCaption.subtitlesEl.addClass('html5');
            state.captionHideTimeout = setTimeout(state.videoCaption.autoHideCaptions, state.videoCaption.fadeOutTimeout);
        }
    }

    // function bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function bindHandlers(state) {
        $(window).bind('resize', state.videoCaption.resize);
        state.videoCaption.hideSubtitlesEl.click(state.videoCaption.toggle);

        state.videoCaption.subtitlesEl
            .on(
                'mouseenter',
                state.videoCaption.onMouseEnter
            ).on(
                'mouseleave',
                state.videoCaption.onMouseLeave
            ).on(
                'mousemove',
                state.videoCaption.onMovement
            ).on(
                'mousewheel',
                state.videoCaption.onMovement
            ).on(
                'DOMMouseScroll',
                state.videoCaption.onMovement
            );

        if (state.videoType === 'html5') {
            state.el.on('mousemove', state.videoCaption.autoShowCaptions)
        }
    }

    function fetchCaption(state) {
        state.videoCaption.hideCaptions(state.hide_captions);

        $.getWithPrefix(captionURL(state), function(captions) {
            state.videoCaption.captions = captions.text;
            state.videoCaption.start = captions.start;
            state.videoCaption.loaded = true;

            if (onTouchBasedDevice()) {
                state.videoCaption.subtitlesEl.find('li').html(
                    'Caption will be displayed when you start playing the video.'
                );
            } else {
                state.videoCaption.renderCaption();
            }
        });
    }

    function captionURL(state) {
        return '' + state.config.caption_asset_path + state.youtubeId('1.0') + '.srt.sjson';
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

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
        this.videoCaption.subtitlesEl.css({
            maxHeight: this.videoCaption.captionHeight()
        });

        this.videoCaption.subtitlesEl
            .find('.spacing:first').height(this.videoCaption.topSpacingHeight())
            .find('.spacing:last').height(this.videoCaption.bottomSpacingHeight());

        this.videoCaption.scrollCaption();
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
        var container, _this = this;
        container = $('<ol>');

        $.each(this.videoCaption.captions, function(index, text) {
            container.append(
                $('<li>').html(text)
                    .data('index', index)
                    .data('start', _this.videoCaption.start[index])
            );
        });

        this.videoCaption.subtitlesEl
            .html(container.html())
            .find('li[data-index]').on('click', this.videoCaption.seekPlayer)
            .prepend(
                $('<li class="spacing">').height(this.videoCaption.topSpacingHeight())
            )
            .append(
                $('<li class="spacing">').height(this.videoCaption.bottomSpacingHeight())
            );

        this.videoCaption.rendered = true;
    }

    function scrollCaption() {
        var el = this.videoCaption.subtitlesEl.find('.current:first');

        if (!this.videoCaption.frozen && el.length) {
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
            time = Math.round(Time.convert(time, this.speed, '1.0') * 1000 + 250);
            newIndex = this.videoCaption.search(time);

            if (newIndex !== void 0 && this.videoCaption.currentIndex !== newIndex) {
                if (this.videoCaption.currentIndex) {
                    this.videoCaption.subtitlesEl.find('li.current').removeClass('current');
                }

                this.videoCaption.subtitlesEl.find("li[data-index='" + newIndex + "']").addClass('current');

                this.videoCaption.currentIndex = newIndex;

                this.videoCaption.scrollCaption();
            }
        }
    }

    function seekPlayer(event) {
        var time;

        event.preventDefault();
        time = Math.round(Time.convert($(event.target).data('start'), '1.0', this.speed) / 1000);

        this.trigger(['videoPlayer', 'onCaptionSeek'], time);
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
        if (hide_captions) {
            this.captionsHidden = true;
            this.videoCaption.hideSubtitlesEl.attr('title', 'Turn on captions');
            this.el.addClass('closed');
        } else {
            this.captionsHidden = false;
            this.videoCaption.hideSubtitlesEl.attr('title', 'Turn off captions');
            this.el.removeClass('closed');
            this.videoCaption.scrollCaption();
        }

        $.cookie('hide_captions', hide_captions, {
            expires: 3650,
            path: '/'
        });
    }

    function captionHeight() {
        if (this.isFullScreen) {
            return $(window).height() - this.el.find('.video-controls').height();
        } else {
            return this.el.find('.video-wrapper').height();
        }
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
