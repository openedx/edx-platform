define([
    'backbone', 'js/models/group'
],
function (Backbone, GroupModel) {
    'use strict';
    var GroupCollection = Backbone.Collection.extend({
        model: GroupModel,
        /**
         * Indicates if the collection is empty when all the models are empty
         * or the collection does not include any models.
         **/
        isEmpty: function() {
            return this.length === 0 || this.every(function(m) {
                return m.isEmpty();
            });
        }
    });

    return GroupCollection;
});
