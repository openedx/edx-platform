define([
    'js/collections/group_configuration', 'js/models/group_configuration', 'js/views/pages/group_configurations'
], function(GroupConfigurationCollection, GroupConfigurationModel, GroupConfigurationsPage) {
    'use strict';
    return function(experimentsEnabled, experimentGroupConfigurationsJson, contentGroupConfigurationJson,
                     groupConfigurationUrl, courseOutlineUrl) {
        var experimentGroupConfigurations = new GroupConfigurationCollection(
                experimentGroupConfigurationsJson, {parse: true}
            ),
            contentGroupConfiguration = new GroupConfigurationModel(contentGroupConfigurationJson, {
                parse: true, canBeEmpty: true
            });

        experimentGroupConfigurations.url = groupConfigurationUrl;
        experimentGroupConfigurations.outlineUrl = courseOutlineUrl;
        contentGroupConfiguration.urlRoot = groupConfigurationUrl;
        contentGroupConfiguration.outlineUrl = courseOutlineUrl;
        new GroupConfigurationsPage({
            el: $('#content'),
            experimentsEnabled: experimentsEnabled,
            experimentGroupConfigurations: experimentGroupConfigurations,
            contentGroupConfiguration: contentGroupConfiguration
        }).render();
    };
});
