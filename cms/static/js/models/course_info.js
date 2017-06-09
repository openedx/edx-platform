define(['backbone'], function(Backbone) {
    // single per course holds the updates and handouts
    var CourseInfo = Backbone.Model.extend({
        // This model class is not suited for restful operations and is considered just a server side initialized container
        url: '',

        defaults: {
            'updates': null,   // UpdateCollection
            'handouts': null    // HandoutCollection
        }
    });
    return CourseInfo;
});
