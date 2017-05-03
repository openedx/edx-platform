(function(requirejs, require, define) {
    'use strict';
    define(
    'video/08_video_auto_advance_control.js', [],
function() {
    /**
     * Auto advance control module.
     * @exports video/08_video_auto_advance_control.js
     * @constructor
     * @param {object} state The object containing the state of the video player.
     * @return {jquery Promise}
     */
    var AutoAdvanceControl = function(state) {
        if (!(this instanceof AutoAdvanceControl)) {
            return new AutoAdvanceControl(state);
        }

        _.bindAll(this, 'onClick', 'destroy', 'autoPlay', 'autoAdvance');
        this.state = state;
        this.state.videoAutoAdvanceControl = this;
        this.initialize();

        return $.Deferred().resolve().promise();
    };

    AutoAdvanceControl.prototype = {
        template: [
            '<button class="control auto-advance" aria-disabled="false" title="',
            gettext('Auto-advance'),
            '">',
            '<span class="label" aria-hidden="true">', gettext('Auto-advance'), '</span>',
            '</button>'
        ].join(''),

        destroy: function() {
            this.el.remove();
            this.state.el.off('destroy', this.destroy);
            delete this.state.videoAutoAdvanceControl;
        },

        /** Initializes the module. */
        initialize: function() {
            var state = this.state;

            this.el = $(this.template);
            this.render();
            this.setAutoAdvance(state.auto_advance);
            this.bindHandlers();

            return true;
        },

        /**
         * Creates any necessary DOM elements, attach them, and set their,
         * initial configuration.
         * @param {boolean} enabled Whether auto advance is enabled
         */
        render: function() {
            this.state.el.find('.secondary-controls').prepend(this.el);
        },

        /**
         * Bind any necessary function callbacks to DOM events (click,
         * mousemove, etc.).
         */
        bindHandlers: function() {
            this.el.on({
                'click': this.onClick
            });
            this.state.el.on({
                'ready': this.autoPlay,
                'ended': this.autoAdvance,
                'destroy': this.destroy
            });
        },

        onClick: function(event) {
            event.preventDefault();
            var enabled = this.state.auto_advance ? false : true;
            this.setAutoAdvance(enabled);
            this.el.trigger('autoadvancechange', [enabled]);
        },

        /**
         * Sets or unsets auto advance.
         * @param {boolean} enabled Sets auto advance.
         */
        setAutoAdvance: function(enabled) {
            if (enabled) {
                this.el.addClass('active')
            } else {
                this.el.removeClass('active')
            }
        },

        autoPlay: function() {
            if (this.state.auto_advance) {
                this.state.videoCommands.execute('play');
            }
        },

        autoAdvance: function() {
            if (this.state.auto_advance) {
                $('.sequence-nav-button.button-next').first().click();
            }
        },
    };

    return AutoAdvanceControl;
});
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
