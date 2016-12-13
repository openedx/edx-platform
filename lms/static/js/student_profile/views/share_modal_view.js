(function(define) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'moment',
            'edx-ui-toolkit/js/utils/html-utils',
            'text!templates/student_profile/share_modal.underscore'],
        function(gettext, $, _, Backbone, Moment, HtmlUtils, badgeModalTemplate) {
            var ShareModalView = Backbone.View.extend({
                attributes: {
                    class: 'badges-overlay'
                },
                template: HtmlUtils.template(badgeModalTemplate),
                events: {
                    'click .badges-modal': function(event) { event.stopPropagation(); },
                    'click .badges-modal .close': 'close',
                    'click .badges-overlay': 'close',
                    keydown: 'keyAction',
                    'focus .focusguard-start': 'focusGuardStart',
                    'focus .focusguard-end': 'focusGuardEnd'
                },

                initialize: function(options) {
                    this.options = _.extend({}, options);
                },

                focusGuardStart: function() {
                    // Should only be selected directly if shift-tabbing from the start, so grab last item.
                    this.$el.find('a').last().focus();
                },

                focusGuardEnd: function() {
                    this.$el.find('.badges-modal').focus();
                },

                close: function() {
                    this.$el.fadeOut('short', 'swing', _.bind(this.remove, this));
                    this.options.shareButton.focus();
                },

                keyAction: function(event) {
                    if (event.keyCode === $.ui.keyCode.ESCAPE) {
                        this.close();
                    }
                },

                ready: function() {
                    // Focusing on the modal background directly doesn't work, probably due
                    // to its positioning.
                    this.$el.find('.badges-modal').focus();
                },

                render: function() {
                    HtmlUtils.setHtml(this.$el, this.template(this.model.toJSON()));
                    return this;
                }
            });

            return ShareModalView;
        });
}).call(this, define || RequireJS.define);
