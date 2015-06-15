// Backbone Application View: Certificates Page

define([ // jshint ignore:line
    'jquery',
    'underscore',
    'gettext',
    'js/views/pages/base_page',
    'js/certificates/views/certificates_list'
],
function ($, _, gettext, BasePage, CertificatesListView) {
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
            this.$('.wrapper-certificates.certificates-list').append(this.certificatesListView.render().el);
            return $.Deferred().resolve().promise();
        }
    });
    return CertificatesPage;
});
