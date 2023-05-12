// eslint-disable-next-line no-undef
define([
    'backbone', 'js/models/group_configuration'
],
function(Backbone, GroupConfigurationModel) {
    'use strict';

    // eslint-disable-next-line no-var
    var GroupConfigurationCollection = Backbone.Collection.extend({
        model: GroupConfigurationModel
    });

    return GroupConfigurationCollection;
});
