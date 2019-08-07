(function(requirejs, require, define) {
    'use strict';
    define(
        'video/08_video_auto_advance_control.js', [
            'edx-ui-toolkit/js/utils/html-utils',
            'underscore'
        ], function(HtmlUtils, _) {
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
                template: HtmlUtils.interpolateHtml(
                    HtmlUtils.HTML([
                        '<button class="control auto-advance" aria-disabled="false" title="',
                        '{autoAdvanceText}',
                        '">',
                        '<span class="label" aria-hidden="true">',
                        '{autoAdvanceText}',
                        '</span>',
                        '</button>'].join('')),
                    {
                        autoAdvanceText: gettext('Auto-advance')
                    }
                ).toString(),

                destroy: function() {
                    this.el.off({
                        click: this.onClick
                    });
                    this.el.remove();
                    this.state.el.off({
                        ready: this.autoPlay,
                        ended: this.autoAdvance,
                        destroy: this.destroy
                    });
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
                        click: this.onClick
                    });
                    this.state.el.on({
                        ready: this.autoPlay,
                        ended: this.autoAdvance,
                        destroy: this.destroy
                    });
                },

                onClick: function(event) {
                    var enabled = !this.state.auto_advance;
                    event.preventDefault();
                    this.setAutoAdvance(enabled);
                    this.el.trigger('autoadvancechange', [enabled]);
                },

                /**
                 * Sets or unsets auto advance.
                 * @param {boolean} enabled Sets auto advance.
                 */
                setAutoAdvance: function(enabled) {
                    if (enabled) {
                        this.el.addClass('active');
                    } else {
                        this.el.removeClass('active');
                    }
                },

                autoPlay: function() {
                    // Only autoplay the video if it's the first component of the unit.
                    // If a unit has more than one video, no more than one will autoplay.
                    var isFirstComponent = this.state.el.parents('.vert-0').length === 1;
                    if (this.state.auto_advance && isFirstComponent) {
                        this.state.videoCommands.execute('play');
                    }
                },

                autoAdvance: function() {
                    if (this.state.auto_advance) {
                        $('.sequence-nav-button.button-next').first().click();
                    }
                }
            };

            return AutoAdvanceControl;
        });
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
