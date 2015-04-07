define([
    'jquery', 'underscore', 'gettext', 'js/views/pages/base_page',
    'js/common_helpers/page_helpers',
    'js/certificates/views/certificates_list'
],
function ($, _, gettext, BasePage, PageHelpers, CertificatesListView) {
    'use strict';
    console.log('certificates_page.start');
    var CertificatesPage = BasePage.extend({
        initialize: function(options) {
            console.log('certificates_page.initialize');
            BasePage.prototype.initialize.call(this);
            this.certificatesCollection = options.certificatesCollection;
            this.certificatesListView = new CertificatesListView({
                collection: this.certificatesCollection
            });

        },


        renderPage: function() {
            console.log('certificates_page.renderPage');
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
            console.log('certificates_page.addWindowActions');
            $(window).on('beforeunload', this.onBeforeUnload.bind(this));
        },

        onBeforeUnload: function () {
            console.log('certificates_page.onBeforeUnload');
            var dirty = this.certificate.isDirty();

            if (dirty) {
                return gettext('You have unsaved changes. Do you really want to leave this page?');
            }
        },
        /**
         * Focus on and expand group configuration with peculiar id.
         * @param {String|Number} Id of the group configuration.
         */
        expandCertificate: function (id) {
            var certificate = this.certificates.findWhere({
                id: parseInt(id)
            });
        }

    });
    console.log('certificates_page.CertificatesPage');
    console.log(CertificatesPage)
    console.log('certificates_page.return');
    return CertificatesPage;
}); // end define();
