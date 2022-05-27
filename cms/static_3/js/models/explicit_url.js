/**
 * A model that simply allows the update URL to be passed
 * in as an argument.
 */
define(['backbone'], function(Backbone) {
    return Backbone.Model.extend({
        defaults: {
            explicit_url: ''
        },
        url: function() {
            return this.get('explicit_url');
        }
    });
});
