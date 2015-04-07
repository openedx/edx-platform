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
            if (hash) {
                // Strip leading '#' to get id string to match
                this.expandCertificate(hash.replace('#', ''));
            }
            return $.Deferred().resolve().promise();
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
