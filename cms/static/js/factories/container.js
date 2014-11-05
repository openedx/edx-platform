define([
    'jquery', 'js/models/xblock_info', 'js/views/pages/container',
    'js/collections/component_template', 'xmodule', 'coffee/src/main',
    'xblock/cms.runtime.v1'
],
function($, XBlockInfo, ContainerPage, ComponentTemplates, xmoduleLoader) {
    'use strict';
    return function (componentTemplates, XBlockInfoJson, action, isUnitPage) {
        var templates = new ComponentTemplates(componentTemplates, {parse: true}),
            mainXBlockInfo = new XBlockInfo(XBlockInfoJson, {parse: true});

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
