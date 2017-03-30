define([
    'js/collections/group_configuration', 'js/models/group_configuration', 'js/views/pages/group_configurations'
], function(GroupConfigurationCollection, GroupConfigurationModel, GroupConfigurationsPage) {
    'use strict';
    return function(experimentsEnabled,
                    experimentGroupConfigurationsJson,
                    allGroupConfigurationJson,
                    groupConfigurationUrl,
                    courseOutlineUrl) {
        var experimentGroupConfigurations = new GroupConfigurationCollection(
                experimentGroupConfigurationsJson, {parse: true}
            ),
            allGroupConfigurations = [],
            newGroupConfig,
            i;

        for (i = 0; i < allGroupConfigurationJson.length; i++) {
            newGroupConfig = new GroupConfigurationModel(allGroupConfigurationJson[i],
                {parse: true, canBeEmpty: true});
            newGroupConfig.urlRoot = groupConfigurationUrl;
            newGroupConfig.outlineUrl = courseOutlineUrl;
            allGroupConfigurations.push(newGroupConfig);
        }

        experimentGroupConfigurations.url = groupConfigurationUrl;
        experimentGroupConfigurations.outlineUrl = courseOutlineUrl;
        new GroupConfigurationsPage({
            el: $('#content'),
            experimentsEnabled: experimentsEnabled,
            experimentGroupConfigurations: experimentGroupConfigurations,
            allGroupConfigurations: allGroupConfigurations
        }).render();
    };
});
