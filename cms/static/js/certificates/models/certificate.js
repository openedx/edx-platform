define([
    'backbone', 'underscore', 'underscore.string', 'gettext', 'backbone.associations', 'coffee/src/main'
],
function(Backbone, _, str, gettext) {
    'use strict';
    console.log('certificate_model.start');
    _.str = str;
    var Certificate = Backbone.Model.extend({
        idAttribute: "id",
        defaults: {
            name: 'Default Name',
            description: 'Default Description',
            version: 1
        },
        parse: function (response) {
            console.log(response.id + " got parse called!");
            return response;
        },

        setOriginalAttributes: function() {
            console.log('certificate_model.setOriginalAttributes');
            this._originalAttributes = this.parse(this.toJSON());
        }
    });

    console.log('certificate_model.Certificate');
    console.log(Certificate)
    console.log("certificate_model.return")
    return Certificate;
});


/*


        defaults: function() {
            console.log('certificate_model.defaults');
            return {
                name: '',
                description: '',
                editing: false,
                usage: []
            };
        },

        relations: [
        ],

        initialize: function(attributes, options) {
            console.log('certificate_model.initialize');
            this.canBeEmpty = options && options.canBeEmpty;
            this.setOriginalAttributes();
            return this;
        },



        reset: function() {
            console.log('certificate_model.reset');
            this.set(this._originalAttributes, { parse: true, validate: true });
        },

        isDirty: function() {
            console.log('certificate_model.isDirty');
            return !_.isEqual(
                this._originalAttributes, this.parse(this.toJSON())
            );
        },

        isEmpty: function() {
            console.log('certificate_model.isEmpty');
            return !this.get('name');
        },

        parse: function(response) {
            var attrs = $.extend(true, {}, response);
            return attrs;
        },

        toJSON: function() {
            console.log('certificate_model.toJSON');
            return {
                id: this.get('id'),
                name: this.get('name'),
                description: this.get('description'),
            };
        },

        validate: function(attrs) {
            console.log('certificate_model.validate');
            if (!_.str.trim(attrs.name)) {
                return {
                    message: gettext('Certificate name is required.'),
                    attributes: {name: true}
                };
            }
        }
*/
