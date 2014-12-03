define([
    'jquery', 'js/collections/checklist', 'js/views/checklist'
], function($, ChecklistCollection, ChecklistView) {
    'use strict';
    return function (handlerUrl) {
        var checklistCollection = new ChecklistCollection(),
            editor;

        checklistCollection.url = handlerUrl;
        editor = new ChecklistView({
            el: $('.course-checklists'),
            collection: checklistCollection
        });
        checklistCollection.fetch({reset: true});
    };
});
