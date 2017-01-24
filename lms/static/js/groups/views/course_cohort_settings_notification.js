(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone', 'gettext'], function($, _, Backbone, gettext) {
        var CourseCohortSettingsNotificationView = Backbone.View.extend({
            initialize: function(options) {
                this.template = _.template($('#cohort-state-tpl').text());
                this.cohortEnabled = options.cohortEnabled;
            },

            render: function() {
                this.$el.html(this.template({}));
                this.showCohortStateMessage();
                return this;
            },

            showCohortStateMessage: function() {
                var actionToggleMessage = this.$('.action-toggle-message');

                AnimationUtil.triggerAnimation(actionToggleMessage);
                if (this.cohortEnabled) {
                    actionToggleMessage.text(gettext('Cohorts Enabled'));
                } else {
                    actionToggleMessage.text(gettext('Cohorts Disabled'));
                }
            }
        });
        return CourseCohortSettingsNotificationView;
    });
}).call(this, define || RequireJS.define);
