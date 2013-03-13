(function (requirejs, require, define) {

// VideoCaption module.
define(
'videoalpha/display/video_caption.js',
['videoalpha/display/bind.js'],
function (bind) {

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
        state.videoCaption.resize              = bind(resize, state);
        state.videoCaption.toggle              = bind(toggle, state);
        state.videoCaption.onMouseEnter        = bind(onMouseEnter, state);
        state.videoCaption.onMouseLeave        = bind(onMouseLeave, state);
        state.videoCaption.onMovement          = bind(onMovement, state);
        state.videoCaption.renderCaption       = bind(renderCaption, state);
        state.videoCaption.captionHeight       = bind(captionHeight, state);
        state.videoCaption.topSpacingHeight    = bind(topSpacingHeight, state);
        state.videoCaption.bottomSpacingHeight = bind(bottomSpacingHeight, state);
        state.videoCaption.scrollCaption       = bind(scrollCaption, state);
        state.videoCaption.search              = bind(search, state);
        state.videoCaption.play                = bind(play, state);
        state.videoCaption.pause               = bind(pause, state);
        state.videoCaption.seekPlayer          = bind(seekPlayer, state);
        state.videoCaption.hideCaptions        = bind(hideCaptions, state);
        state.videoCaption.calculateOffset     = bind(calculateOffset, state);
        state.videoCaption.updatePlayTime      = bind(updatePlayTime, state);
    }

    // function renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function renderElements(state) {
        state.videoCaption.loaded = false;

        state.videoCaption.subtitlesEl = $('<ol class="subtitles"></ol>');
        state.videoCaption.hideSubtitlesEl = $(
            '<a href="#" class="hide-subtitles" title="Turn off captions">Captions</a>'
        );

        state.el.find('.video-wrapper').after(state.videoCaption.subtitlesEl);
        state.el.find('.video-controls .secondary-controls').append(state.videoCaption.hideSubtitlesEl);

        state.el.find('.subtitles').css({
            'maxHeight': state.el.find('.video-wrapper').height() - 5
        });

        fetchCaption(state);
    }

    // function bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function bindHandlers(state) {
        $(window).bind('resize', state.videoCaption.resize);
        state.videoCaption.hideSubtitlesEl.click(state.videoCaption.toggle);
        state.videoCaption.subtitlesEl.mouseenter(
            state.videoCaption.onMouseEnter
        ).mouseleave(
            state.videoCaption.onMouseLeave
        ).mousemove(
            state.videoCaption.onMovement
        ).bind(
            'mousewheel',
            state.videoCaption.onMovement
        ).bind(
            'DOMMouseScroll',
            state.videoCaption.onMovement
        );
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
        console.log('We are inside captionURL() function.');
        console.log('state.config.caption_asset_path = "' + state.config.caption_asset_path + '".');
        console.log('state.youtubeId("1.0") = "' + state.youtubeId('1.0') + '".');

        return '' + state.config.caption_asset_path + state.youtubeId('1.0') + '.srt.sjson';
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function resize() {
        this.videoCaption.subtitlesEl.css({
            'maxHeight': this.videoCaption.captionHeight()
        });

        this.videoCaption.subtitlesEl.find('.spacing:first').height(this.videoCaption.topSpacingHeight());
        this.videoCaption.subtitlesEl.find('.spacing:last').height(this.videoCaption.bottomSpacingHeight());

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
        var container, _this;

        _this = this;
        container = $('<ol>');

        $.each(this.videoCaption.captions, function(index, text) {
            container.append($('<li>').html(text).attr({
                'data-index': index,
                'data-start': _this.videoCaption.start[index]
            }));
        });

        this.videoCaption.subtitlesEl.html(container.html());
        this.videoCaption.subtitlesEl.find('li[data-index]').on('click', this.videoCaption.seekPlayer);
        this.videoCaption.subtitlesEl.prepend(
            $('<li class="spacing">').height(this.videoCaption.topSpacingHeight())
        ).append(
            $('<li class="spacing">').height(this.videoCaption.bottomSpacingHeight())
        );

        this.videoCaption.rendered = true;
    }

    function scrollCaption() {
        if (!this.videoCaption.frozen && this.videoCaption.subtitlesEl.find('.current:first').length) {
            this.videoCaption.subtitlesEl.scrollTo(this.videoCaption.subtitlesEl.find('.current:first'), {
                'offset': -this.videoCaption.calculateOffset(this.videoCaption.subtitlesEl.find('.current:first'))
            });
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

        this.trigger(['videoPlayer', 'onSeek'], time, 'method');
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
            this.videoCaption.hideSubtitlesEl.attr('title', 'Turn on captions');
            this.el.addClass('closed');
        } else {
            this.videoCaption.hideSubtitlesEl.attr('title', 'Turn off captions');
            this.el.removeClass('closed');
            this.videoCaption.scrollCaption();
        }

        $.cookie('hide_captions', hide_captions, {
            'expires': 3650,
            'path': '/'
        });
    }

    function captionHeight() {
        if (this.el.hasClass('fullscreen')) {
            return $(window).height() - this.el.find('.video-controls').height();
        } else {
            return this.el.find('.video-wrapper').height();
        }
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
