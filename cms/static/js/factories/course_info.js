// eslint-disable-next-line no-undef
define([
    'jquery', 'js/collections/course_update', 'js/models/module_info',
    'js/models/course_info', 'js/views/course_info_edit'
], function($, CourseUpdateCollection, ModuleInfoModel, CourseInfoModel, CourseInfoEditView) {
    'use strict';

    return function(updatesUrl, handoutsLocator, baseAssetUrl) {
        /* eslint-disable-next-line camelcase, no-var */
        var course_updates = new CourseUpdateCollection(),
            // eslint-disable-next-line camelcase
            course_handouts, editor;

        // eslint-disable-next-line camelcase
        course_updates.url = updatesUrl;
        // eslint-disable-next-line camelcase
        course_updates.fetch({reset: true});
        // eslint-disable-next-line camelcase
        course_handouts = new ModuleInfoModel({
            id: handoutsLocator
        });
        editor = new CourseInfoEditView({
            el: $('.main-wrapper'),
            model: new CourseInfoModel({
                // eslint-disable-next-line camelcase
                updates: course_updates,
                base_asset_url: baseAssetUrl,
                // eslint-disable-next-line camelcase
                handouts: course_handouts
            })
        });
        editor.render();
    };
});
