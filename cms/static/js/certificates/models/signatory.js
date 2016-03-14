// Backbone.js Application Model: Certificate Signatory

define([ // jshint ignore:line
    'underscore',
    'underscore.string',
    'backbone',
    'backbone-relational',
    'gettext'
],
function(_, str, Backbone, BackboneRelational, gettext) {
    'use strict';
    _.str = str;

    var Signatory = Backbone.RelationalModel.extend({
        idAttribute: "id",
        defaults: {
            name: '',
            title: '',
            organization: '',
            signature_image_path: ''
        },

        initialize: function() {
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
        },

        reset: function() {
            // Revert the attributes of this model instance back to initial state
            this.set(this._originalAttributes, { parse: true, validate: true });
        }
    });
    return Signatory;
});
