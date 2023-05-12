// Backbone Application View: Certificates Page

// eslint-disable-next-line no-undef
define([
    'jquery',
    'underscore',
    'gettext',
    'js/views/pages/base_page',
    'js/certificates/views/certificates_list'
],
function($, _, gettext, BasePage, CertificatesListView) {
    'use strict';

    // eslint-disable-next-line no-var
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
            this.$('.wrapper-certificates.certificates-list').append(this.certificatesListView.render().el);
            return $.Deferred().resolve().promise();
        }
    });
    return CertificatesPage;
});
