define([
    'jquery', 'js/collections/course_update', 'js/models/module_info',
    'js/models/course_info', 'js/views/course_info_edit'
], function($, CourseUpdateCollection, ModuleInfoModel, CourseInfoModel, CourseInfoEditView) {
    'use strict';
    return function (updatesUrl, handoutsLocator, baseAssetUrl, push_notification_enabled) {
        var course_updates = new CourseUpdateCollection(),
            course_handouts, editor;

        course_updates.url = updatesUrl;
        course_updates.fetch({reset: true});
        course_handouts = new ModuleInfoModel({
            id: handoutsLocator
        });
        editor = new CourseInfoEditView({
            el: $('.main-wrapper'),
            model : new CourseInfoModel({
                updates : course_updates,
                base_asset_url : baseAssetUrl,
                handouts : course_handouts
            }),
            push_notification_enabled: push_notification_enabled
        });
        editor.render();
    };
});
