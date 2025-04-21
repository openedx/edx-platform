/* eslint-disable no-console, no-param-reassign */
'use strict';

import _ from 'underscore';

// HTML5Video object that will be exported
const HTML5Video = {};

// Constants mimicking the YouTube API
HTML5Video.PlayerState = {
    UNSTARTED: -1,
    ENDED: 0,
    PLAYING: 1,
    PAUSED: 2,
    BUFFERING: 3,
    CUED: 5
};

// HTML5Video.Player constructor function
class Player {
    constructor(el, config) {
        this.init(el, config);

        const sourceList = $.map(config.videoSources, source => {
            const separator = source.indexOf('?') === -1 ? '?' : '&';
            return `<source src="${source}${separator}${Date.now()}" />`;
        });

        const errorMessage = [
            gettext('This browser cannot play .mp4, .ogg, or .webm files.'),
            gettext('Try using a different browser, such as Google Chrome.')
        ].join('');

        this.video.innerHTML = sourceList.join('') + errorMessage;

        const lastSource = this.videoEl.find('source').last();
        lastSource.on('error', this.showErrorMessage.bind(this));
        lastSource.on('error', this.onError.bind(this));
        this.videoEl.on('error', this.onError.bind(this));
    }

    init(el, config) {
        const self = this;
        const isTouch = window.onTouchBasedDevice?.() || '';
        const events = [
            'loadstart', 'progress', 'suspend', 'abort', 'error',
            'emptied', 'stalled', 'play', 'pause', 'loadedmetadata',
            'loadeddata', 'waiting', 'playing', 'canplay', 'canplaythrough',
            'seeking', 'seeked', 'timeupdate', 'ended', 'ratechange',
            'durationchange', 'volumechange'
        ];

        this.config = config;
        this.logs = [];
        this.el = $(el);

        this.video = document.createElement('video');
        this.videoEl = $(this.video);
        this.videoOverlayEl = this.el.find('.video-wrapper .btn-play');
        this.playerState = HTML5Video.PlayerState.UNSTARTED;

        _.bindAll(this, 'onLoadedMetadata', 'onPlay', 'onPlaying', 'onPause', 'onEnded');

        const togglePlayback = () => {
            const { PLAYING, PAUSED } = HTML5Video.PlayerState;
            if (self.playerState === PLAYING) {
                self.playerState = PAUSED;
                self.pauseVideo();
            } else {
                self.playerState = PLAYING;
                self.playVideo();
            }
        };

        this.videoEl.on('click', togglePlayback);
        this.videoOverlayEl.on('click', togglePlayback);

        this.debug = false;

        $.each(events, (index, eventName) => {
            self.video.addEventListener(eventName, function (...args) {
                self.logs.push({
                    'event name': eventName,
                    state: self.playerState
                });

                if (self.debug) {
                    console.log(
                        'event name:', eventName,
                        'state:', self.playerState,
                        'readyState:', self.video.readyState,
                        'networkState:', self.video.networkState
                    );
                }

                self.el.trigger(`html5:${eventName}`, args);
            });
        });

        this.video.addEventListener('loadedmetadata', this.onLoadedMetadata, false);
        this.video.addEventListener('play', this.onPlay, false);
        this.video.addEventListener('playing', this.onPlaying, false);
        this.video.addEventListener('pause', this.onPause, false);
        this.video.addEventListener('ended', this.onEnded, false);

        if (/iP(hone|od)/i.test(isTouch[0])) {
            this.videoEl.prop('controls', true);
        }

        if (config.poster) {
            this.videoEl.prop('poster', config.poster);
        }

        this.videoEl.appendTo(this.el.find('.video-player > div:first-child'));
    }

    showPlayButton() {
        this.videoOverlayEl.removeClass('is-hidden');
    }

    hidePlayButton() {
        this.videoOverlayEl.addClass('is-hidden');
    }

    showLoading() {
        this.el
            .removeClass('is-initialized')
            .find('.spinner')
            .removeAttr('tabindex')
            .attr({ 'aria-hidden': 'false' });
    }

    hideLoading() {
        this.el
            .addClass('is-initialized')
            .find('.spinner')
            .attr({ 'aria-hidden': 'false', tabindex: -1 });
    }

    updatePlayerLoadingState(state) {
        if (state === 'show') {
            this.hidePlayButton();
            this.showLoading();
        } else if (state === 'hide') {
            this.hideLoading();
        }
    }

    callStateChangeCallback() {
        const callback = this.config.events.onStateChange;
        if ($.isFunction(callback)) {
            callback({ data: this.playerState });
        }
    }

    pauseVideo() {
        this.video.pause();
    }

    seekTo(value) {
        if (typeof value === 'number' && value <= this.video.duration && value >= 0) {
            this.video.currentTime = value;
        }
    }

    setVolume(value) {
        if (typeof value === 'number' && value <= 100 && value >= 0) {
            this.video.volume = value * 0.01;
        }
    }

    getCurrentTime() {
        return this.video.currentTime;
    }

    playVideo() {
        this.video.play();
    }

    getPlayerState() {
        return this.playerState;
    }

    getVolume() {
        return this.video.volume;
    }

    getDuration() {
        return isNaN(this.video.duration) ? 0 : this.video.duration;
    }

    setPlaybackRate(value) {
        const newSpeed = parseFloat(value);
        if (isFinite(newSpeed) && this.video.playbackRate !== value) {
            this.video.playbackRate = value;
        }
    }

    getAvailablePlaybackRates() {
        return [0.75, 1.0, 1.25, 1.5, 2.0];
    }

    _getLogs() {
        return this.logs;
    }

    showErrorMessage(_, cssSelector = '.video-player .video-error') {
        this.el
            .find('.video-player div')
            .addClass('hidden')
            .end()
            .find(cssSelector)
            .removeClass('is-hidden')
            .end()
            .addClass('is-initialized')
            .find('.spinner')
            .attr({ 'aria-hidden': 'true', tabindex: -1 });
    }

    onError() {
        const callback = this.config.events.onError;
        if ($.isFunction(callback)) {
            callback();
        }
    }

    destroy() {
        this.video.removeEventListener('loadedmetadata', this.onLoadedMetadata, false);
        this.video.removeEventListener('play', this.onPlay, false);
        this.video.removeEventListener('playing', this.onPlaying, false);
        this.video.removeEventListener('pause', this.onPause, false);
        this.video.removeEventListener('ended', this.onEnded, false);

        this.el
            .find('.video-player div')
            .removeClass('is-hidden')
            .end()
            .find('.video-player .video-error')
            .addClass('is-hidden')
            .end()
            .removeClass('is-initialized')
            .find('.spinner')
            .attr({ 'aria-hidden': 'false' });

        this.videoEl.off('remove');
        this.videoEl.remove();
    }

    onReady() {
        if ($.isFunction(this.config.events.onReady)) {
            this.config.events.onReady(null);
        }
        this.showPlayButton();
    }

    onLoadedMetadata() {
        this.playerState = HTML5Video.PlayerState.PAUSED;
        if ($.isFunction(this.config.events.onReady)) {
            this.onReady();
        }
    }

    onPlay() {
        this.playerState = HTML5Video.PlayerState.BUFFERING;
        this.callStateChangeCallback();
        this.videoOverlayEl.addClass('is-hidden');
    }

    onPlaying() {
        this.playerState = HTML5Video.PlayerState.PLAYING;
        this.callStateChangeCallback();
        this.videoOverlayEl.addClass('is-hidden');
    }

    onPause() {
        this.playerState = HTML5Video.PlayerState.PAUSED;
        this.callStateChangeCallback();
        this.showPlayButton();
    }

    onEnded() {
        this.playerState = HTML5Video.PlayerState.ENDED;
        this.callStateChangeCallback();
    }
}

// Attach to exported object
HTML5Video.Player = Player;

export { HTML5Video };