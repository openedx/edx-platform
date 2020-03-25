(function(define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'common/js/components/utils/view_utils',
        'teams/js/views/team_utils',
        'text!teams/templates/manage.underscore'
    ], function(Backbone, _, gettext, HtmlUtils, ViewUtils, TeamUtils, manageTemplate) {
        var ManageView = Backbone.View.extend({

            srInfo: {
                id: 'heading-manage',
                text: gettext('Manage')
            },

            events: {
                'click #download-team-csv': 'downloadCsv',
                'change #upload-team-csv-input': 'setTeamMembershipCsv',
                'click #upload-team-csv': ViewUtils.withDisabledElement('uploadCsv')
            },

            initialize: function(options) {
                this.teamEvents = options.teamEvents;
                this.csvUploadUrl = options.teamMembershipManagementUrl;
                this.csvDownloadUrl = options.teamMembershipManagementUrl;
            },

            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    HtmlUtils.template(manageTemplate)({})
                );
                return this;
            },

            downloadCsv: function() {
                window.location.href = this.csvDownloadUrl;
            },

            setTeamMembershipCsv: function(event) {
                this.membershipFile = event.target.files[0];
            },

            uploadCsv: function() {
                var self = this;
                var formData = new FormData();
                formData.append('csv', this.membershipFile);

                return $.ajax({
                    type: 'POST',
                    url: self.csvUploadUrl,
                    data: formData,
                    processData: false,  // tell jQuery not to process the data
                    contentType: false   // tell jQuery not to set contentType
                }).done(
                    self.handleCsvUploadSuccess
                ).fail(
                    self.handleCsvUploadFailure
                );
            },

            handleCsvUploadSuccess: function(data) {
                TeamUtils.showInfoBanner(data.message, false);

                // This handler is currently unimplemented (TODO MST-44)
                // this.teamEvents.trigger('teams:update', {});
            },

            handleCsvUploadFailure: function(jqXHR) {
                TeamUtils.showInfoBanner(jqXHR.responseJSON.errors, true);
            }
        });
        return ManageView;
    });
}).call(this, define || RequireJS.define);
