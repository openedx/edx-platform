define(['backbone', 'underscore'], function(Backbone, _) {
    /**
     * Model for Tag count view
     */
    var TagCountModel = Backbone.Model.extend({
        defaults: {
            content_id: null,
            tags_count: 0,
            course_authoring_url: null,
        },
    });
    return TagCountModel;
});
