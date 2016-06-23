define([
    'js/models/explicit_url', 'js/views/tabs', 'xmodule', 'js/main', 'xblock/cms.runtime.v1'
], function (TabsModel, TabsEditView, xmoduleLoader) {
    'use strict';
    return function (courseLocation, explicitUrl) {
        xmoduleLoader.done(function () {
            var model = new TabsModel({
                    id: courseLocation,
                    explicit_url: explicitUrl
                }),
                editView;

            editView = new TabsEditView({
                el: $('.tab-list'),
                model: model,
                mast: $('.wrapper-mast')
            });
        });
    };
});
