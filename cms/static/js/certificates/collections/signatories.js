define([
    'backbone', 'js/certificates/models/signatory'
],
function(Backbone, Signatory) {
    'use strict';
    console.log("signatory_collection.start");
    var SignatoryCollection = Backbone.Collection.extend({
        model: Signatory,
        initialize: function(attr, options) {
            //TODO: You can ignore the signatories URL (format) at this time.
            //TODO: 0 is pointing to id of certificate, it needs to be dynamic as well.
            this.url = options.certificateUrl + '/0/signatories';
        }
    });
    console.log("signatory_collection.SignatoryCollection");
    console.log(SignatoryCollection);
    console.log("signatory_collection.return");
    return SignatoryCollection;
});
