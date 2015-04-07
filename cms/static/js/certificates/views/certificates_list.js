/**
 * This class defines a list view for course certificates.
 * It is expected to be backed by a CertificatesCollection.
 */
define([
    'js/views/list', 'js/certificates/views/certificate_item', 'gettext'
], function(ListView, CertificateItemView, gettext) {
    'use strict';
    console.log('certificates_list.start');
    var CertificatesListView = ListView.extend({
        tagName: 'div',
        className: 'certificates-list',
        newModelOptions: {},

        // Translators: this refers to a collection of certificates.
        itemCategoryDisplayName: gettext('certificate'),

        emptyMessage: gettext('You have not created any certificates yet.'),

        createItemView: function(options) {
            console.log('certificates_list.createItemView');
            return new CertificateItemView(options);
        }


    });

    console.log('certificates_list.CertificatesListView');
    console.log(CertificatesListView);
    console.log('certificates_list.return');
    return CertificatesListView;
});
