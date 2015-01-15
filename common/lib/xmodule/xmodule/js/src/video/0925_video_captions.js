(function (define) {

// VideoOverlayCaptions module.
define(
"video/0925_video_captions.js",
[],
function () {

    var VideoOverlayCaptions = function (state) {
        if (!(this instanceof VideoOverlayCaptions)) {
            return new VideoOverlayCaptions(state);
        }

        this.state = state;
        this.state.videoCaption = this;
        this.renderElements();
        this.bindHandlers();

        return $.Deferred().resolve().promise();
    };

    VideoOverlayCaptions.prototype = {

        renderElements: function () {
            var state = this.state;

            this.captionsContainerEl = state.el.find('.video-overlay-captions');
            this.captionsToggleButtonEl = state.el.find('.captions');
            this.transcriptContainer = $('#transcript-captions');
        },

        bindHandlers: function () {
            var self = this,
                state = this.state;

            this.captionsToggleButtonEl.on('click', this.toggle.bind(this));
        },

        getHighlightedTextInTranscript: function (cc_is_visible) {
            var self = this,
                transcript = $('#transcript-captions li.current').text();

            this.captionsContainerEl.text(transcript);
            this.listenForHighlightChange();
            this.listenForDraggabilly();
        },

        listenForHighlightChange: function (cc_is_visible) {
            var self = this;

            setTimeout(function() {
                self.getHighlightedTextInTranscript();
            }, 500);
        },

        toggle: function (event) {
            event.preventDefault();

            if (this.state.el.hasClass('cc-on')) {
                this.toggleCaptions(false);
            } else {
                this.toggleCaptions(true);
            }
        },

        toggleCaptions: function (cc_is_visible, update_cookie) {
            var captionsToggleButtonEl = this.captionsToggleButtonEl,
                state = this.state,
                type,
                text,
                active_class,
                visible_class,
                aria;

            if (typeof update_cookie === 'undefined') {
                update_cookie = true;
            }

            if (cc_is_visible) {
                type = cc_is_visible;
                state.el.addClass('cc-on');
                active_class = 'is-active';
                visible_class = 'is-visible';
                aria = 'true';
                text = gettext('Turn off closed-captioning');
                // this.listenForDraggabilly(true);
            } else {
                type = cc_is_visible;
                state.el.removeClass('cc-on');
                active_class = '';
                visible_class = '';
                aria = 'false';
                text = gettext('Turn on closed-captioning');
                // this.listenForDraggabilly(false);
            }

            captionsToggleButtonEl
                .attr('title', text)
                .attr('aria-pressed', aria)
                .removeClass('is-active')
                .addClass(active_class)
                .find('.sr')
                    .text(gettext(text));

            this.captionsContainerEl
                .removeClass('is-visible')
                .addClass(visible_class);

            this.getHighlightedTextInTranscript(cc_is_visible);
            this.listenForHighlightChange(cc_is_visible);

            if (update_cookie) {
                $.cookie('closed_captions', cc_is_visible, {
                    expires: 3650,
                    path: '/'
                });
            }
        },

        listenForDraggabilly: function (draggie_status) {
            var captions = document.querySelector('.video-overlay-captions');

            if (captions) {
                draggie = new Draggabilly(captions, { containment: true });
            }
        }
    };

    return VideoOverlayCaptions;
});

}(RequireJS.define));
