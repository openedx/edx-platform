(function(define) {
    'use strict';

    define([
        'jquery',
        'underscore',
        'backbone',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function($, _, Backbone, gettext, HtmlUtils) {
        // eslint-disable-next-line no-var
        var CourseCohortSettingsNotificationView = Backbone.View.extend({
            initialize: function(options) {
                this.template = HtmlUtils.template($('#cohort-state-tpl').text());
                this.cohortEnabled = options.cohortEnabled;
            },

            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    this.template({})
                );
                this.showCohortStateMessage();
                return this;
            },

            showCohortStateMessage: function() {
                // eslint-disable-next-line no-var
                var actionToggleMessage = this.$('.action-toggle-message');

                // eslint-disable-next-line no-undef
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
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
