
import { interpolateHtml, HTML } from 'edx-ui-toolkit/js/utils/html-utils';
import _ from 'underscore';
import * as gettext from 'gettext';

/**
 * Creates the VideoQualityControl module.
 * @param {object} state The object containing the state of the video player.
 * @returns {Promise<void>|undefined} A promise that resolves when the module is initialized, or undefined if not applicable.
 */
const VideoQualityControl = function (state) {
    // Changing quality for now only works for YouTube videos.
    if (state.videoType !== 'youtube') {
        return;
    }

    this.state = state;
    this.videoQualityControl = {
        el: null,
        quality: 'large'
    };

    this._makeFunctionsPublic(state);
    this._renderElements(state);
    this._bindHandlers(state);

    return Promise.resolve();
};

/**
 * Makes the VideoQualityControl functions accessible via the 'state' object.
 * @param {object} state The object containing the state of the video player.
 */
VideoQualityControl.prototype._makeFunctionsPublic = function (state) {
    const methodsDict = {
        destroy: this.destroy.bind(this),
        fetchAvailableQualities: this.fetchAvailableQualities.bind(this),
        onQualityChange: this.onQualityChange.bind(this),
        showQualityControl: this.showQualityControl.bind(this),
        toggleQuality: this.toggleQuality.bind(this)
    };

    state.bindTo(methodsDict, state.videoQualityControl, state);
};

VideoQualityControl.prototype.template = interpolateHtml(
    HTML([
        '<button class="control quality-control is-hidden" aria-disabled="false" title="',
        '{highDefinition}',
        '">',
        '<span class="icon icon-hd" aria-hidden="true">HD</span>',
        '<span class="sr text-translation">',
        '{highDefinition}',
        '</span>&nbsp;',
        '<span class="sr control-text">',
        '{off}',
        '</span>',
        '</button>'
    ].join('')),
    {
        highDefinition: gettext('High Definition'), // Assuming gettext is globally available or imported
        off: gettext('off') // Assuming gettext is globally available or imported
    }
);

VideoQualityControl.prototype.destroy = function () {
    if (this.videoQualityControl.el) {
        this.videoQualityControl.el.removeEventListener('click', this.videoQualityControl.toggleQuality);
        this.videoQualityControl.el.remove();
    }
    if (this.state && this.state.el) {
        this.state.el.removeEventListener('play.quality', this.fetchAvailableQualities);
        this.state.el.removeEventListener('destroy.quality', this.destroy);
    }
    delete this.state.videoQualityControl;
};

/**
 * Creates and appends the DOM elements for the quality control.
 * @param {object} state The object containing the state of the video player.
 */
VideoQualityControl.prototype._renderElements = function (state) {
    this.videoQualityControl.el = this.createDOMElement(this.template.toString());
    const secondaryControls = state.el.querySelector('.secondary-controls');
    if (secondaryControls && this.videoQualityControl.el) {
        secondaryControls.appendChild(this.videoQualityControl.el);
    }
};

/**
 * Creates a DOM element from an HTML string.
 * @param {string} htmlString The HTML string to create the element from.
 * @returns {HTMLElement} The created DOM element.
 */
VideoQualityControl.prototype.createDOMElement = function (htmlString) {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlString.trim();
    return tempDiv.firstChild;
};

/**
 * Binds event handlers for the quality control.
 * @param {object} state The object containing the state of the video player.
 */
VideoQualityControl.prototype._bindHandlers = function (state) {
    if (this.videoQualityControl.el) {
        this.videoQualityControl.el.addEventListener('click', this.toggleQuality);
    }
    if (state && state.el) {
        state.el.addEventListener('play', this.fetchAvailableQualities.bind(this), { once: true });
        state.el.addEventListener('destroy', this.destroy.bind(this));
    }
};

/**
 * Shows the quality control button. This function will only be called if HD qualities are available.
 */
VideoQualityControl.prototype.showQualityControl = function () {
    if (this.videoQualityControl.el) {
        this.videoQualityControl.el.classList.remove('is-hidden');
    }
};

/**
 * Gets the available qualities from the YouTube API. Possible values are:
 * ['highres', 'hd1080', 'hd720', 'large', 'medium', 'small'].
 * HD are: ['highres', 'hd1080', 'hd720'].
 */
VideoQualityControl.prototype.fetchAvailableQualities = function () {
    if (this.state && this.state.videoPlayer && this.state.videoPlayer.player && this.state.videoPlayer.player.getAvailableQualityLevels) {
        const qualities = this.state.videoPlayer.player.getAvailableQualityLevels();
        this.state.config.availableHDQualities = _.intersection(
            qualities, ['highres', 'hd1080', 'hd720']
        );

        // HD qualities are available, show video quality control.
        if (this.state.config.availableHDQualities.length > 0) {
            this.showQualityControl();
            this.onQualityChange(this.videoQualityControl.quality);
        }
        // On initialization, force the video quality to be 'large' instead of
        // 'default'. Otherwise, the player will sometimes switch to HD
        // automatically, for example when the iframe resizes itself.
        this.state.trigger('videoPlayer.handlePlaybackQualityChange',
            this.videoQualityControl.quality
        );
    }
};

/**
 * Updates the visual state of the quality control button based on the current quality.
 * @param {string} value The current quality level.
 */
VideoQualityControl.prototype.onQualityChange = function (value) {
    this.videoQualityControl.quality = value;
    if (this.videoQualityControl.el) {
        const controlTextSpan = this.videoQualityControl.el.querySelector('.control-text');
        if (_.contains(this.state.config.availableHDQualities, value)) {
            this.videoQualityControl.el.classList.add('active');
            if (controlTextSpan) {
                controlTextSpan.textContent = gettext('on'); // Assuming gettext is globally available or imported
            }
        } else {
            this.videoQualityControl.el.classList.remove('active');
            if (controlTextSpan) {
                controlTextSpan.textContent = gettext('off'); // Assuming gettext is globally available or imported
            }
        }
    }
};

/**
 * Toggles the quality of the video if HD qualities are available.
 * @param {Event} event The click event.
 */
VideoQualityControl.prototype.toggleQuality = function (event) {
    event.preventDefault();
    if (this.state && this.state.config && this.state.config.availableHDQualities) {
        const currentValue = this.videoQualityControl.quality;
        const isHD = _.contains(this.state.config.availableHDQualities, currentValue);
        const newQuality = isHD ? 'large' : 'highres';
        this.state.trigger('videoPlayer.handlePlaybackQualityChange', newQuality);
    }
};

export {VideoQualityControl};