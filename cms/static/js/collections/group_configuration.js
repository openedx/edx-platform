define([
    'backbone', 'js/models/group_configuration'
],
function(Backbone, GroupConfigurationModel) {
    'use strict';
    var GroupConfigurationCollection = Backbone.Collection.extend({
        model: GroupConfigurationModel
    });

    return GroupConfigurationCollection;
});
