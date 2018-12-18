// Backbone.js Application Collection: Certificates

define([
    'backbone',
    'gettext',
    'js/certificates/models/certificate'
],
function(Backbone, gettext, Certificate) {
    'use strict';
    var CertificateCollection = Backbone.Collection.extend({
        model: Certificate,

        /**
         * It represents the maximum number of certificates that a user can create. default set to 1.
         */
        maxAllowed: 1,

        initialize: function(attr, options) {
            // Set up the attributes for this collection instance
            this.url = options.certificateUrl;
            this.bind('remove', this.onModelRemoved, this);
            this.bind('add', this.onModelAdd, this);
        },

        certificateArray: function(certificateInfo) {
            var returnArray;
            try {
                returnArray = JSON.parse(certificateInfo);
            } catch (ex) {
                // If it didn't parse, and `certificateInfo` is an object then return as it is
                // otherwise return empty array
                if (typeof certificateInfo === 'object') {
                    returnArray = certificateInfo;
                } else {
                    returnArray = [];
                }
            }
            return returnArray;
        },

        onModelRemoved: function() {
            // remove the certificate web preview UI.
            if (window.certWebPreview && this.length === 0) {
                window.certWebPreview.remove();
            }
            this.toggleAddNewItemButtonState();
        },

        onModelAdd: function() {
            this.toggleAddNewItemButtonState();
        },

        toggleAddNewItemButtonState: function() {
            // user can create a new item e.g certificate; if not exceeded the maxAllowed limit.
            if (this.length >= this.maxAllowed) {
                $('.action-add').addClass('action-add-hidden');
            } else {
                $('.action-add').removeClass('action-add-hidden');
            }
        },

        parse: function(certificatesJson) {
            // Transforms the provided JSON into a Certificates collection
            var modelArray = this.certificateArray(certificatesJson);
            modelArray.forEach(function(item) {
                this.push(item);
            }, this);
            return this.models;
        }
    });
    return CertificateCollection;
});
