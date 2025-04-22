// VideoControl.js

import * as Time from 'time.js';

/**
 * Initializes video control logic.
 * @param {Object} state - The shared state object for the video player.
 * @returns {Promise<void>}
 */
export default function VideoControl(state) {
  return new Promise((resolve) => {
    state.videoControl = {};

    _makeFunctionsPublic(state);
    _renderElements(state);
    _bindHandlers(state);

    resolve();
  });
}

// ***************************************************************
// Private helper functions
// ***************************************************************

function _makeFunctionsPublic(state) {
  const methodsDict = {
    destroy,
    hideControls,
    show,
    showControls,
    focusFirst,
    updateVcrVidTime
  };

  // Equivalent of `state.bindTo(methodsDict, state.videoControl, state)`
  for (const [key, fn] of Object.entries(methodsDict)) {
    state.videoControl[key] = fn.bind(state);
  }
}

function destroy() {
  this.el.removeEventListener('mousemove', this.videoControl.showControls);
  this.el.removeEventListener('keydown', this.videoControl.showControls);
  this.el.removeEventListener('destroy', this.videoControl.destroy);
  this.el.removeEventListener('initialize', this.videoControl.focusFirst);

  if (this.controlHideTimeout) {
    clearTimeout(this.controlHideTimeout);
  }

  delete this.videoControl;
}

function _renderElements(state) {
  state.videoControl.el = state.el.querySelector('.video-controls');
  state.videoControl.vidTimeEl = state.videoControl.el.querySelector('.vidtime');

  if (state.videoType === 'html5' && state.config.autohideHtml5) {
    state.videoControl.fadeOutTimeout = state.config.fadeOutTimeout;

    state.videoControl.el.classList.add('html5');

    state.controlHideTimeout = setTimeout(
      state.videoControl.hideControls,
      state.videoControl.fadeOutTimeout
    );
  }
}

function _bindHandlers(state) {
  if (state.videoType === 'html5' && state.config.autohideHtml5) {
    state.el.addEventListener('mousemove', state.videoControl.showControls);
    state.el.addEventListener('keydown', state.videoControl.showControls);
  }

  if (state.config.focusFirstControl) {
    state.el.addEventListener('initialize', state.videoControl.focusFirst);
  }

  state.el.addEventListener('destroy', state.videoControl.destroy);
}

// ***************************************************************
// Public methods — bound to state.videoControl
// ***************************************************************

function focusFirst() {
  const firstControl = this.videoControl.el.querySelector('.vcr a, .vcr button');
  if (firstControl) firstControl.focus();
}

function show() {
  this.videoControl.el.classList.remove('is-hidden');
  const event = new CustomEvent('controls:show', { detail: arguments });
  this.el.dispatchEvent(event);
}

function showControls() {
  if (this.controlShowLock || !this.captionsHidden) return;

  this.controlShowLock = true;

  const el = this.videoControl.el;

  switch (this.controlState) {
    case 'invisible':
      el.style.display = 'block';
      this.controlState = 'visible';
      break;

    case 'hiding':
      el.style.opacity = 1;
      el.style.display = 'block';
      this.controlState = 'visible';
      break;

    case 'visible':
      clearTimeout(this.controlHideTimeout);
      break;
  }

  this.controlHideTimeout = setTimeout(
    this.videoControl.hideControls,
    this.videoControl.fadeOutTimeout
  );

  this.controlShowLock = false;
}

function hideControls() {
  if (!this.captionsHidden) return;

  this.controlHideTimeout = null;
  this.controlState = 'hiding';

  const el = this.videoControl.el;
  el.style.transition = `opacity ${this.videoControl.fadeOutTimeout}ms`;
  el.style.opacity = 0;

  setTimeout(() => {
    el.style.display = 'none';
    this.controlState = 'invisible';

    this.videoVolumeControl?.el.classList.remove('open');
    this.videoSpeedControl?.el.classList.remove('open');

    this.focusGrabber?.enableFocusGrabber?.();
  }, this.videoControl.fadeOutTimeout);
}

function updateVcrVidTime(params) {
  let endTime = this.config.endTime ?? params.duration;
  endTime = Math.min(endTime, params.duration);

  const startTime = this.config.startTime > 0 ? this.config.startTime : 0;
  if (startTime && this.config.endTime) {
    endTime = this.config.endTime - startTime;
  }

  const currentTime = startTime ? params.time - startTime : params.time;
  const formattedTime = `${Time.format(currentTime)} / ${Time.format(endTime)}`;

  if (this.videoControl.vidTimeEl) {
    this.videoControl.vidTimeEl.textContent = formattedTime;
  }
}
