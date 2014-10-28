define([
    'js/collections/group_configuration', 'js/views/pages/group_configurations'
], function(GroupConfigurationCollection, GroupConfigurationsPage) {
    'use strict';
    return function (configurations, groupConfigurationUrl, courseOutlineUrl) {
        var collection = new GroupConfigurationCollection(configurations, { parse: true }),
            configurationsPage;

        collection.url = groupConfigurationUrl;
        collection.outlineUrl = courseOutlineUrl;
        configurationsPage = new GroupConfigurationsPage({
            el: $('#content'),
            collection: collection
        }).render();
    };
});
