define([
    'jquery', 'underscore', 'js/models/xblock_info', 'js/views/pages/paged_container',
    'js/views/library_container', 'js/collections/component_template', 'xmodule', 'js/main',
    'xblock/cms.runtime.v1'
],
function($, _, XBlockInfo, PagedContainerPage, LibraryContainerView, ComponentTemplates, xmoduleLoader) {
    'use strict';
    return function (componentTemplates, XBlockInfoJson, options) {
        var main_options = {
            el: $('#content'),
            model: new XBlockInfo(XBlockInfoJson, {parse: true}),
            templates: new ComponentTemplates(componentTemplates, {parse: true}),
            action: 'view',
            viewClass: LibraryContainerView,
            canEdit: true
        };

        xmoduleLoader.done(function () {
            var view = new PagedContainerPage(_.extend(main_options, options));
            view.render();
        });
    };
});
