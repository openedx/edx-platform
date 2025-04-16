'use strict';

import $ from 'jquery';
import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';
import { gettext } from '@edx/frontend-platform/i18n';

const fullscreenTemplate = `
  <button class="control add-fullscreen" aria-disabled="false" title="${gettext('Fill browser')}" aria-label="${gettext('Fill browser')}">
    <span class="icon fa fa-arrows-alt" aria-hidden="true"></span>
  </button>
`;

const prefixedFullscreenProperties = (() => {
    if ('fullscreenEnabled' in document) {
        return {
            fullscreenElement: 'fullscreenElement',
            fullscreenEnabled: 'fullscreenEnabled',
            requestFullscreen: 'requestFullscreen',
            exitFullscreen: 'exitFullscreen',
            fullscreenchange: 'fullscreenchange',
            fullscreenerror: 'fullscreenerror'
        };
    }
    if ('webkitFullscreenEnabled' in document) {
        return {
            fullscreenElement: 'webkitFullscreenElement',
            fullscreenEnabled: 'webkitFullscreenEnabled',
            requestFullscreen: 'webkitRequestFullscreen',
            exitFullscreen: 'webkitExitFullscreen',
            fullscreenchange: 'webkitfullscreenchange',
            fullscreenerror: 'webkitfullscreenerror'
        };
    }
    if ('mozFullScreenEnabled' in document) {
        return {
            fullscreenElement: 'mozFullScreenElement',
            fullscreenEnabled: 'mozFullScreenEnabled',
            requestFullscreen: 'mozRequestFullScreen',
            exitFullscreen: 'mozCancelFullScreen',
            fullscreenchange: 'mozfullscreenchange',
            fullscreenerror: 'mozfullscreenerror'
        };
    }
    if ('msFullscreenEnabled' in document) {
        return {
            fullscreenElement: 'msFullscreenElement',
            fullscreenEnabled: 'msFullscreenEnabled',
            requestFullscreen: 'msRequestFullscreen',
            exitFullscreen: 'msExitFullscreen',
            fullscreenchange: 'MSFullscreenChange',
            fullscreenerror: 'MSFullscreenError'
        };
    }
    return {};
})();

function getVendorPrefixed(property) {
    return prefixedFullscreenProperties[property];
}

function getFullscreenElement() {
    return document[getVendorPrefixed('fullscreenElement')];
}

function exitFullscreen() {
    return document[getVendorPrefixed('exitFullscreen')]?.() || null;
}

function requestFullscreen(element, options) {
    return element[getVendorPrefixed('requestFullscreen')]?.(options) || null;
}

function renderElements(state) {
    const { videoFullScreen } = state;
    videoFullScreen.fullScreenEl = $(fullscreenTemplate);
    videoFullScreen.sliderEl = state.el.find('.slider');
    videoFullScreen.fullScreenState = false;
    HtmlUtils.append(state.el.find('.secondary-controls'), HtmlUtils.HTML(videoFullScreen.fullScreenEl));
    videoFullScreen.updateControlsHeight();
}

function bindHandlers(state) {
    const { videoFullScreen } = state;

    videoFullScreen.fullScreenEl.on('click', videoFullScreen.toggleHandler);
    state.el.on({ destroy: videoFullScreen.destroy });
    $(document).on('keyup', videoFullScreen.exitHandler);
    document.addEventListener(getVendorPrefixed('fullscreenchange'), videoFullScreen.handleFullscreenChange);
}

function getControlsHeight(controls, slider) {
    return controls.height() + 0.5 * slider.height();
}

function destroy() {
    $(document).off('keyup', this.videoFullScreen.exitHandler);
    this.videoFullScreen.fullScreenEl.remove();
    this.el.off({ destroy: this.videoFullScreen.destroy });

    document.removeEventListener(
        getVendorPrefixed('fullscreenchange'),
        this.videoFullScreen.handleFullscreenChange
    );

    if (this.isFullScreen) {
        this.videoFullScreen.exit();
    }

    delete this.videoFullScreen;
}

function handleFullscreenChange() {
    if (getFullscreenElement() !== this.el[0] && this.isFullScreen) {
        this.videoFullScreen.handleExit();
    }
}

function updateControlsHeight() {
    const controls = this.el.find('.video-controls');
    const slider = this.videoFullScreen.sliderEl;

    this.videoFullScreen.height = getControlsHeight(controls, slider);
    return this.videoFullScreen.height;
}

function notifyParent(fullscreenOpen) {
    if (window !== window.parent) {
        window.parent.postMessage({
            type: 'plugin.videoFullScreen',
            payload: { open: fullscreenOpen }
        }, document.referrer);
    }
}

function toggleHandler(event) {
    event.preventDefault();
    this.videoCommands.execute('toggleFullScreen');
}

function handleExit() {
    if (!this.isFullScreen) return;

    const fullScreenClassNameEl = this.el.add(document.documentElement);
    const closedCaptionsEl = this.el.find('.closed-captions');

    this.isFullScreen = this.videoFullScreen.fullScreenState = false;
    fullScreenClassNameEl.removeClass('video-fullscreen');
    $(window).scrollTop(this.scrollPos);

    this.videoFullScreen.fullScreenEl
        .attr({ title: gettext('Fill browser'), 'aria-label': gettext('Fill browser') })
        .find('.icon')
        .removeClass('fa-compress')
        .addClass('fa-arrows-alt');

    $(closedCaptionsEl).css({ top: '70%', left: '5%' });

    if (this.resizer) {
        this.resizer.delta.reset().setMode('width');
    }

    this.el.trigger('fullscreen', [this.isFullScreen]);
    this.videoFullScreen.notifyParent(false);
}

function handleEnter() {
    if (this.isFullScreen) return;

    const fullScreenClassNameEl = this.el.add(document.documentElement);
    const closedCaptionsEl = this.el.find('.closed-captions');

    this.videoFullScreen.notifyParent(true);

    this.isFullScreen = this.videoFullScreen.fullScreenState = true;
    fullScreenClassNameEl.addClass('video-fullscreen');

    this.videoFullScreen.fullScreenEl
        .attr({ title: gettext('Exit full browser'), 'aria-label': gettext('Exit full browser') })
        .find('.icon')
        .removeClass('fa-arrows-alt')
        .addClass('fa-compress');

    $(closedCaptionsEl).css({ top: '70%', left: '5%' });

    if (this.resizer) {
        this.resizer.delta.substract(this.videoFullScreen.updateControlsHeight(), 'height').setMode('both');
    }

    this.el.trigger('fullscreen', [this.isFullScreen]);
}

function enter() {
    this.scrollPos = $(window).scrollTop();
    this.videoFullScreen.handleEnter();
    requestFullscreen(this.el[0]);
}

function exit() {
    if (getFullscreenElement() === this.el[0]) {
        exitFullscreen();
    } else {
        this.videoFullScreen.handleExit();
    }
}

function toggle() {
    if (this.videoFullScreen.fullScreenState) {
        this.videoFullScreen.exit();
    } else {
        this.videoFullScreen.enter();
    }
}

function exitHandler(event) {
    if (this.isFullScreen && event.keyCode === 27) {
        event.preventDefault();
        this.videoCommands.execute('toggleFullScreen');
    }
}

function makeFunctionsPublic(state) {
    const methods = {
        destroy,
        enter,
        exit,
        exitHandler,
        handleExit,
        handleEnter,
        handleFullscreenChange,
        toggle,
        toggleHandler,
        updateControlsHeight,
        notifyParent
    };

    state.bindTo(methods, state.videoFullScreen, state);
}

function initializeVideoFullScreen(state) {
    const dfd = $.Deferred();

    state.videoFullScreen = {};
    makeFunctionsPublic(state);
    renderElements(state);
    bindHandlers(state);

    dfd.resolve();
    return dfd.promise();
}

export { initializeVideoFullScreen }