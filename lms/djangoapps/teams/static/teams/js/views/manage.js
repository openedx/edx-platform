(function(define) {
    'use strict';

    define([
        'backbone',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'common/js/components/utils/view_utils',
        'teams/js/views/team_utils',
        'text!teams/templates/manage.underscore',
        'text!teams/templates/manage-table.underscore'
    ], function(Backbone, _, gettext, HtmlUtils, ViewUtils, TeamUtils, manageTemplate, manageTableTemplate) {
        var ManageView = Backbone.View.extend({

            srInfo: {
                id: 'heading-manage',
                text: gettext('Manage')
            },

            events: {
                'click #download-team-csv': 'downloadCsv',
                'change #upload-team-csv-input': 'setTeamMembershipCsv',
                'click #upload-team-csv': ViewUtils.withDisabledElement('uploadCsv'),
                'click #load-manage-team-button': 'loadManageTeamTable',
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
                this.delegateEvents(this.events);
                return this;
            },

            downloadCsv: function() {
                window.location.href = this.csvDownloadUrl;
            },

            setTeamMembershipCsv: function(event) {
                this.membershipFile = event.target.files[0];

                // enable the upload button when a file is selected
                if (this.membershipFile) {
                    $('#upload-team-csv').removeClass('is-disabled').attr('aria-disabled', false);
                } else {
                    $('#upload-team-csv').addClass('is-disabled').attr('aria-disabled', true);
                }
            },

            teamTableLoading: function() {
                const teamTable = $('.team-table-wrapper');
                const loadButton = $('.load-manage-team-button');
                loadButton.addClass('is-disabled').attr('aria-disabled', true);
                HtmlUtils.setHtml(
                    teamTable,
                    "Loading.."
                );
            },

            loadManageTeamTable: function(event) {
                this.teamTableLoading();
                $.ajax({
                    type: 'get',
                    url: this.csvUploadUrl,
                    data: {fmt: 'json'}
                }).done(
                    this.renderManageTeamsTable
                ).fail(
                    this.handleManageTeamsTableFailure
                );
            },

            renderManageTeamsTable: function(data) {
                TeamUtils.showInfoBanner("Table Loaded", false);
                const teamTable = $('.team-table-wrapper');
                console.log(data);
                HtmlUtils.setHtml(
                    teamTable,
                    HtmlUtils.template(manageTableTemplate)({data: data})
                );
            },

            handleCsvUploadFailure: function(jqXHR) {
                TeamUtils.showInfoBanner(jqXHR, true);
            },

            uploadCsv: function() {
                var formData = new FormData();
                formData.append('csv', this.membershipFile); // xss-lint: disable=javascript-jquery-append

                return $.ajax({
                    type: 'POST',
                    url: this.csvUploadUrl,
                    data: formData,
                    processData: false, // tell jQuery not to process the data
                    contentType: false // tell jQuery not to set contentType
                }).done(
                    this.handleCsvUploadSuccess
                ).fail(
                    this.handleCsvUploadFailure
                );
            },

            handleCsvUploadSuccess: function(data) {
                TeamUtils.showInfoBanner(data.message, false);

                // Implement a teams:update event (TODO MST-44)
            },

            handleCsvUploadFailure: function(jqXHR) {
                TeamUtils.showInfoBanner(jqXHR.responseJSON.errors, true);
            }
        });
        return ManageView;
    });
}).call(this, define || RequireJS.define);
