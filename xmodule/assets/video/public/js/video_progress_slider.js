'use strict';
import $ from 'jquery';
import edx from 'edx-ui-toolkit/js/utils/html-utils';
import { gettext, ngettext, interpolate } from '@edx/frontend-platform/i18n';

/**
 * "This is as true in everyday life as it is in battle: we are given one life
 * and the decision is ours whether to wait for circumstances to make up our
 * mind, or whether to act, and in acting, to live."
 * — Omar N. Bradley
 */

const sliderTemplate = `
  <div class="slider" role="application" title="${gettext('Video position. Press space to toggle playback')}"></div>
`;

export default function initializeVideoProgressSlider(state) {
    const dfd = $.Deferred();
    state.videoProgressSlider = {};
    makeFunctionsPublic(state);
    renderElements(state);
    dfd.resolve();
    return dfd.promise();
}

function makeFunctionsPublic(state) {
    const methods = {
        destroy,
        buildSlider,
        getRangeParams,
        onSlide,
        onStop,
        updatePlayTime,
        updateStartEndTimeRegion,
        notifyThroughHandleEnd,
        getTimeDescription,
        focusSlider
    };

    state.bindTo(methods, state.videoProgressSlider, state);
}

function renderElements(state) {
    state.videoProgressSlider.el = $(sliderTemplate);
    state.el.find('.video-controls').prepend(state.videoProgressSlider.el);
    state.videoProgressSlider.buildSlider();
    buildHandle(state);
    bindHandlers(state);
}

function bindHandlers(state) {
    state.videoProgressSlider.el.on('keypress', sliderToggle.bind(state));
    state.el.on('destroy', state.videoProgressSlider.destroy);
}

function destroy() {
    this.videoProgressSlider.el.removeAttr('tabindex').slider('destroy');
    this.el.off('destroy', this.videoProgressSlider.destroy);
    delete this.videoProgressSlider;
}

function buildHandle(state) {
    const handle = state.videoProgressSlider.el.find('.ui-slider-handle');
    state.videoProgressSlider.handle = handle;

    state.videoProgressSlider.el.attr({ tabindex: -1 });

    handle.attr({
        role: 'slider',
        'aria-disabled': false,
        'aria-valuetext': getTimeDescription(state.videoProgressSlider.slider.slider('option', 'value')),
        'aria-valuemax': state.videoPlayer.duration(),
        'aria-valuemin': '0',
        'aria-valuenow': state.videoPlayer.currentTime,
        tabindex: '0',
        'aria-label': gettext('Video position. Press space to toggle playback')
    });
}

function buildSlider() {
    const sliderContents = edx.HtmlUtils.joinHtml(
        edx.HtmlUtils.HTML('<div class="ui-slider-handle progress-handle"></div>')
    );

    this.videoProgressSlider.el.append(sliderContents.text);

    this.videoProgressSlider.slider = this.videoProgressSlider.el.slider({
        range: 'min',
        min: this.config.startTime,
        max: this.config.endTime,
        slide: this.videoProgressSlider.onSlide,
        stop: this.videoProgressSlider.onStop,
        step: 5
    });

    this.videoProgressSlider.sliderProgress = this.videoProgressSlider.slider.find(
        '.ui-slider-range.ui-widget-header.ui-slider-range-min'
    );
}

function updateStartEndTimeRegion(params) {
    if (!params.duration) return;

    let start = this.config.startTime;
    let end = this.config.endTime;
    const duration = params.duration;

    if (start > duration) start = 0;
    else if (this.isFlashMode()) start /= Number(this.speed);

    if (end === null || end > duration) end = duration;
    else if (this.isFlashMode()) end /= Number(this.speed);

    if (start === 0 && end === duration) return;

    return getRangeParams(start, end, duration);
}

function getRangeParams(startTime, endTime, duration) {
    const step = 100 / duration;
    const left = startTime * step;
    const width = endTime * step - left;

    return {
        left: `${left}%`,
        width: `${width}%`
    };
}

function onSlide(event, ui) {
    const time = ui.value;
    let endTime = this.videoPlayer.duration();

    if (this.config.endTime) {
        endTime = Math.min(this.config.endTime, endTime);
    }

    this.videoProgressSlider.frozen = true;
    this.videoProgressSlider.lastSeekValue = time;

    this.trigger('videoControl.updateVcrVidTime', { time, duration: endTime });
    this.trigger('videoPlayer.onSlideSeek', { type: 'onSlideSeek', time });

    this.videoProgressSlider.handle.attr('aria-valuetext', getTimeDescription(this.videoPlayer.currentTime));
}

function onStop(event, ui) {
    const _this = this;
    this.videoProgressSlider.frozen = true;

    if (this.videoProgressSlider.lastSeekValue !== ui.value) {
        this.trigger('videoPlayer.onSlideSeek', { type: 'onSlideSeek', time: ui.value });
    }

    this.videoProgressSlider.handle.attr('aria-valuetext', getTimeDescription(this.videoPlayer.currentTime));

    setTimeout(() => {
        _this.videoProgressSlider.frozen = false;
    }, 200);
}

function updatePlayTime(params) {
    const time = Math.floor(params.time);
    let endTime = Math.floor(params.duration);

    if (this.config.endTime !== null) {
        endTime = Math.min(this.config.endTime, endTime);
    }

    if (this.videoProgressSlider.slider && !this.videoProgressSlider.frozen) {
        this.videoProgressSlider.slider
            .slider('option', 'max', endTime)
            .slider('option', 'value', time);
    }

    this.videoProgressSlider.handle.attr({
        'aria-valuemax': endTime,
        'aria-valuenow': time
    });
}

function notifyThroughHandleEnd(params) {
    const handle = this.videoProgressSlider.handle;
    if (params.end) {
        handle.attr('title', gettext('Video ended')).focus();
    } else {
        handle.attr('title', gettext('Video position'));
    }
}

function getTimeDescription(time) {
    let seconds = Math.floor(time);
    let minutes = Math.floor(seconds / 60);
    let hours = Math.floor(minutes / 60);

    seconds %= 60;
    minutes %= 60;

    const i18n = (value, word) => {
        let msg;
        switch (word) {
            case 'hour':
                msg = ngettext('%(value)s hour', '%(value)s hours', value);
                break;
            case 'minute':
                msg = ngettext('%(value)s minute', '%(value)s minutes', value);
                break;
            case 'second':
                msg = ngettext('%(value)s second', '%(value)s seconds', value);
                break;
        }
        return interpolate(msg, { value }, true);
    };

    if (hours) {
        return `${i18n(hours, 'hour')} ${i18n(minutes, 'minute')} ${i18n(seconds, 'second')}`;
    } else if (minutes) {
        return `${i18n(minutes, 'minute')} ${i18n(seconds, 'second')}`;
    }

    return i18n(seconds, 'second');
}

function focusSlider() {
    this.videoProgressSlider.handle.attr(
        'aria-valuetext', getTimeDescription(this.videoPlayer.currentTime)
    );
    this.videoProgressSlider.el.trigger('focus');
}

function sliderToggle(e) {
    if (e.which === 32) {
        e.preventDefault();
        this.videoCommands.execute('togglePlayback');
    }
}
