var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.groups = edx.groups || {};

    edx.groups.CourseCohortSettingsNotificationView = Backbone.View.extend({
        initialize: function(options) {
            this.template = _.template($('#cohort-state-tpl').text());
            this.cohortEnabled = options.cohortEnabled;
        },

        render: function() {
            this.$el.html(this.template({}));
            this.showCohortStateMessage();
            return this;
        },

        showCohortStateMessage: function () {
            var actionToggleMessage = this.$('.action-toggle-message');

            // The following lines are necessary to re-trigger the CSS animation on span.action-toggle-message
            actionToggleMessage.removeClass('is-fleeting');
            actionToggleMessage.offset().width = actionToggleMessage.offset().width;
            actionToggleMessage.addClass('is-fleeting');

            if (this.cohortEnabled) {
                actionToggleMessage.text(gettext('Cohorts Enabled'));
            } else {
                actionToggleMessage.text(gettext('Cohorts Disabled'));
            }
        }
    });
}).call(this, $, _, Backbone, gettext);
