import { interpolateHtml, HTML } from 'edx-ui-toolkit/js/utils/html-utils';
import _ from 'underscore';
import * as gettext from 'gettext';

/**
 * Auto advance control module.
 * @exports video/08_video_auto_advance_control.js
 * @constructor
 * @param {object} state The object containing the state of the video player.
 * @return {Promise<void>}
 */
class AutoAdvanceControl {
    constructor(state) {
        if (!(this instanceof AutoAdvanceControl)) {
            return new AutoAdvanceControl(state);
        }

        _.bindAll(this, 'onClick', 'destroy', 'autoPlay', 'autoAdvance');
        this.state = state;
        this.state.videoAutoAdvanceControl = this;
        this.el = null;
        this.initialize();

        return Promise.resolve();
    }

    template = interpolateHtml(
        HTML([
            '<button class="control auto-advance" aria-disabled="false" title="',
            '{autoAdvanceText}',
            '">',
            '<span class="label" aria-hidden="true">',
            '{autoAdvanceText}',
            '</span>',
            '</button>'].join('')),
        {
            autoAdvanceText: gettext('Auto-advance') // Assuming gettext is globally available or imported
        }
    ).toString();

    destroy() {
        if (this.el) {
            this.el.removeEventListener('click', this.onClick);
            this.el.remove();
        }
        if (this.state && this.state.el) {
            this.state.el.removeEventListener('ready', this.autoPlay);
            this.state.el.removeEventListener('ended', this.autoAdvance);
            this.state.el.removeEventListener('destroy', this.destroy);
        }
        if (this.state) {
            delete this.state.videoAutoAdvanceControl;
        }
    }

    /** Initializes the module. */
    initialize() {
        const state = this.state;

        this.el = this.createDOMElement(this.template);
        this.render();
        this.setAutoAdvance(state.auto_advance);
        this.bindHandlers();

        return true;
    }

    /**
     * Creates a DOM element from an HTML string.
     * @param {string} htmlString The HTML string to create the element from.
     * @returns {HTMLElement} The created DOM element.
     */
    createDOMElement(htmlString) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlString.trim();
        return tempDiv.firstChild;
    }

    /**
     * Creates any necessary DOM elements, attach them, and set their,
     * initial configuration.
     * @param {boolean} enabled Whether auto advance is enabled
     */
    render() {
        const secondaryControls = this.state.el.querySelector('.secondary-controls');
        if (secondaryControls && this.el) {
            secondaryControls.prepend(this.el);
        }
    }

    /**
     * Bind any necessary function callbacks to DOM events (click,
     * mousemove, etc.).
     */
    bindHandlers() {
        if (this.el) {
            this.el.addEventListener('click', this.onClick);
        }
        if (this.state && this.state.el) {
            this.state.el.addEventListener('ready', this.autoPlay);
            this.state.el.addEventListener('ended', this.autoAdvance);
            this.state.el.addEventListener('destroy', this.destroy);
        }
    }

    onClick(event) {
        const enabled = !this.state.auto_advance;
        event.preventDefault();
        this.setAutoAdvance(enabled);
        if (this.el) {
            this.el.dispatchEvent(new CustomEvent('autoadvancechange', { detail: [enabled] }));
        }
    }

    /**
     * Sets or unsets auto advance.
     * @param {boolean} enabled Sets auto advance.
     */
    setAutoAdvance(enabled) {
        if (this.el) {
            if (enabled) {
                this.el.classList.add('active');
            } else {
                this.el.classList.remove('active');
            }
        }
    }

    autoPlay() {
        // Only autoplay the video if it's the first component of the unit.
        // If a unit has more than one video, no more than one will autoplay.
        const isFirstComponent = this.state.el.closest('.vert-0');
        if (this.state.auto_advance && isFirstComponent) {
            this.state.videoCommands.execute('play'); // Assuming videoCommands is on the state
        }
    }

    autoAdvance() {
        if (this.state.auto_advance) {
            const nextButton = document.querySelector('.sequence-nav-button.button-next');
            if (nextButton) {
                nextButton.click();
            }
        }
    }
}

export { AutoAdvanceControl };