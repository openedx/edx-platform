// Backbone.js Application Model: Certificate Signatory

define([
    'backbone', 'underscore', 'underscore.string', 'gettext', 'backbone-relational'
],
function(Backbone, _, str) {
    'use strict';
    _.str = str;

    var Signatory = Backbone.RelationalModel.extend({
        idAttribute: "id",
        defaults: {
            name: 'Signatory Name',
            title: 'Signatory Title'
        },

        initialize: function(attributes, options) {
            // Set up the initial state of the attributes set for this model instance
            this.setOriginalAttributes();
            return this;
        },

        parse: function (response) {
            // Parse must be defined for the model, but does not need to do anything special right now
            return response;
        },

        setOriginalAttributes: function() {
            // Remember the current state of this model (enables edit->cancel use cases)
            this._originalAttributes = this.parse(this.toJSON());
        }
    });
    return Signatory;
});
