define([
    'backbone', 'underscore', 'underscore.string', 'gettext', 'backbone-relational'
],
function(Backbone, _, str) {
    'use strict';
    console.log('signatory_relational_model.start');
    _.str = str;

    var Signatory = Backbone.RelationalModel.extend({
        idAttribute: "id",
        defaults: {
            name: 'Signatory name',
            title: 'Signatory title'
        },

        initialize: function(attributes, options) {
            console.log('signatory_model.initialize');
            this.setOriginalAttributes();
            return this;
        },
        parse: function (response) {
            console.log(response.id + " got parse called!");
            return response;
        },

        setOriginalAttributes: function() {
            console.log('signatory_model.setOriginalAttributes');
            this._originalAttributes = this.parse(this.toJSON());
        }
    });

    console.log('signatory_relational_model');
    console.log(Signatory)
    return Signatory;
});
