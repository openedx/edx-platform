import $ from 'jquery'; // jQuery import
import _ from 'underscore';

'use strict';

/**
 * VideoSkipControl function
 *
 * @constructor
 * @param {Object} state The object containing the state of the video
 * @param {Object} i18n The object containing strings with translations
 * @return {jQuery.Promise} Returns a resolved jQuery promise
 */
function VideoSkipControl(state, i18n) {
    if (!(this instanceof VideoSkipControl)) {
        return new VideoSkipControl(state, i18n);
    }

    _.bindAll(this, 'onClick', 'render', 'destroy');
    this.state = state;
    this.state.videoSkipControl = this;
    this.i18n = i18n;

    this.initialize();

    return $.Deferred().resolve().promise();
}

VideoSkipControl.prototype = {
    template: [
        '<button class="control video_control skip skip-control" aria-disabled="false" title="',
        gettext('Do not show again'),
        '">',
        '<span class="icon fa fa-step-forward" aria-hidden="true"></span>',
        '</button>',
    ].join(''),

    initialize: function () {
        this.el = $(this.template);
        this.bindHandlers();
    },

    /** Creates any necessary DOM elements, attach them, and set their, initial configuration. */
    render: function () {
        this.state.el.find('.vcr .control').after(this.el);
    },

    /** Bind any necessary function callbacks to DOM events. */
    bindHandlers: function () {
        this.el.on('click', this.onClick);

        this.state.el.on({
            'play.skip': _.once(this.render),
            'destroy.skip': this.destroy,
        });
    },

    onClick: function (event) {
        event.preventDefault();
        this.state.videoCommands.execute('skip', true);
    },

    destroy: function () {
        this.el.remove();
        this.state.el.off('.skip');
        delete this.state.videoSkipControl;
    },
};

export {VideoSkipControl};