define([
    'js/collections/group_configuration', 'js/models/group_configuration', 'js/views/pages/group_configurations'
], function(GroupConfigurationCollection, GroupConfigurationModel, GroupConfigurationsPage) {
    'use strict';
    return function (experimentsEnabled, experimentConfigurations, cohortConfiguration, groupConfigurationUrl, courseOutlineUrl) {
        var experimentGroupsCollection = new GroupConfigurationCollection(experimentConfigurations, {parse: true}),
            cohortGroupConfiguration = new GroupConfigurationModel(cohortConfiguration, {parse: true});

        experimentGroupsCollection.url = groupConfigurationUrl;
        cohortGroupConfiguration.urlRoot = groupConfigurationUrl;
        experimentGroupsCollection.outlineUrl = courseOutlineUrl;
        new GroupConfigurationsPage({
            el: $('#content'),
            experimentsEnabled: experimentsEnabled,
            experimentGroupsCollection: experimentGroupsCollection,
            cohortGroupConfiguration: cohortGroupConfiguration
        }).render();
    };
});
