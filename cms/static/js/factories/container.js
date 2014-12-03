define([
    'jquery', 'js/models/xblock_info', 'js/views/pages/container',
    'js/collections/component_template', 'xmodule', "js/views/metadata", "js/collections/metadata", 'coffee/src/main',
    'xblock/cms.runtime.v1'
],
function($, XBlockInfo, ContainerPage, ComponentTemplates, xmoduleLoader, MetadataView, MetadataCollection) {
    'use strict';
    return function (componentTemplates, XBlockInfoJson, action, isUnitPage) {
        var templates = new ComponentTemplates(componentTemplates, {parse: true}),
            mainXBlockInfo = new XBlockInfo(XBlockInfoJson, {parse: true});

        window.MetadataView = MetadataView;
        window.MetadataCollection = MetadataCollection;
        xmoduleLoader.done(function () {
            var view = new ContainerPage({
                el: $('#content'),
                model: mainXBlockInfo,
                action: action,
                templates: templates,
                isUnitPage: isUnitPage
            });
            view.render();
        });
    };
});
