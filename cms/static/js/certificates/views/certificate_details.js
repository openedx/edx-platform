/**
 * This class defines a details view for course certificates.
 * It is expected to be instantiated with a Certificate model.
 */
define([
    'js/views/baseview', 'underscore', 'js/certificates/models/signatory', 'js/certificates/views/signatory_details', 'gettext', 'underscore.string'
],
function(BaseView, _, Signatory, SignatoryDetails, gettext, str) {
    'use strict';
    console.log('certificate_details.start');
    var CertificateDetailsView = BaseView.extend({
        tagName: 'div',
        events: {
            'click .edit': 'editCertificate',
            'click .show-details': 'showDetails',
            'click .hide-details': 'hideDetails'
        },

        className: function () {
            console.log('certificate_details.className');
            var index = this.model.collection.indexOf(this.model);

            return [
                'collection',
                'certificates',
                'certificate-details',
                'certificate-details-' + index
            ].join(' ');
        },

        initialize: function() {
            console.log('certificate_details.initialize');
            this.template = _.template(
                $('#certificate-details-tpl').text()
            );
            this.listenTo(this.model, 'change', this.render);
        },

        editCertificate: function(event) {
            console.log('certificate_details.editCertificate');
            if (event && event.preventDefault) { event.preventDefault(); }
            this.model.set('editing', true);
        },

        showDetails: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.render(true);
        },

        hideDetails: function(event) {
            if (event && event.preventDefault) { event.preventDefault(); }
            this.render(false);
        },

        render: function(showDetails) {
            console.log('certificate_details.render');
            var attrs = $.extend({}, this.model.attributes, {
                index: this.model.collection.indexOf(this.model),
                showDetails: showDetails || false
            });

            this.$el.html(this.template(attrs));

            if(showDetails) {
                var self = this;
                this.model.get("signatories").each(function (modelSignatory) {
                    var signatory_detail_view = new SignatoryDetails({model: modelSignatory});
                    self.$('div.signatory-details-list').append($(signatory_detail_view.render().$el));
                });
            }


            return this;
        }

    });

    console.log('certificate_details.CertificateDetailsView');
    console.log(CertificateDetailsView);
    console.log('certificate_details.return');
    return CertificateDetailsView;
});
