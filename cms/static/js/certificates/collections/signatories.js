// Backbone.js Application Collection: Certificate Signatories

define([
    'backbone',
    'js/certificates/models/signatory'
],
function(Backbone, Signatory) {
    'use strict';
    var SignatoryCollection = Backbone.Collection.extend({
        model: Signatory
    });
    return SignatoryCollection;
});
