define([
    'jquery', 'underscore', 'js/models/xblock_container_info', 'js/views/pages/container',
    'js/collections/component_template', 'xmodule', 'cms/js/main',
    'xblock/cms.runtime.v1'
],
function($, _, XBlockContainerInfo, ContainerPage, ComponentTemplates, xmoduleLoader) {
    'use strict';
    return function (componentTemplates, XBlockInfoJson, action, options) {
        var main_options = {
            el: $('#content'),
            model: new XBlockContainerInfo(XBlockInfoJson, {parse: true}),
            action: action,
            templates: new ComponentTemplates(componentTemplates, {parse: true})
        };

        xmoduleLoader.done(function () {
            var view = new ContainerPage(_.extend(main_options, options));
            view.render();
        });
    };
});
