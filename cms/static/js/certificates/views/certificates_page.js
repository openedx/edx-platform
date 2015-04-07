// Backbone Application View: Certificates Page

define([
    'jquery', 'underscore', 'gettext', 'js/views/pages/base_page',
    'js/common_helpers/page_helpers',
    'js/certificates/views/certificates_list'
],
function ($, _, gettext, BasePage, PageHelpers, CertificatesListView) {
    'use strict';
    var CertificatesPage = BasePage.extend({

        initialize: function(options) {
            // Set up the initial state of this object instance
            BasePage.prototype.initialize.call(this);
            this.certificatesCollection = options.certificatesCollection;
            this.certificatesListView = new CertificatesListView({
                collection: this.certificatesCollection
            });

        },

        renderPage: function() {
            // Override the base operation with a class-specific workflow
            var hash = PageHelpers.getLocationHash();
            this.$('.wrapper-certificates.certificates-list').append(this.certificatesListView.render().el);
            this.addWindowActions();
            if (hash) {
                // Strip leading '#' to get id string to match
                this.expandCertificate(hash.replace('#', ''));
            }
            return $.Deferred().resolve().promise();
        },

        addWindowActions: function () {
            // Bind the object to the beforeunload event
            $(window).on('beforeunload', this.onBeforeUnload.bind(this));
        },

        onBeforeUnload: function () {
            // Check to see if there are any pending changes prior to cancelling and notify the user
            if (this.certificate.isDirty()) {
                return gettext('You have unsaved changes. Do you really want to leave this page?');
            }
        },

        expandCertificate: function (id) {
            // Locate the certificate having a corresponding identifier
            var certificate = this.certificates.findWhere({
                id: parseInt(id)
            });
        }
    });
    return CertificatesPage;
});
