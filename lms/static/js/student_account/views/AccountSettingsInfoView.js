var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.AccountSettingsInfoView = Backbone.View.extend({
        events: {
        },

        initialize: function(options) {
            this.template = _.template($('#account_settings_info-tpl').text());
        },

        render: function() {
            this.$el.html(this.template({
                username: this.model.get('username'),
                fullname: this.model.get('name')
            }));
            return this;
        }
    });
}).call(this, $, _, Backbone, gettext);
