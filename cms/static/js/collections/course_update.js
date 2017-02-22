define(['backbone', 'js/models/course_update'], function(Backbone, CourseUpdateModel) {
    /*
        The intitializer of this collection must set id to the update's location.url and courseLocation to the course's location. Must pass the
        collection of updates as [{ date : "month day", content : "html"}]
    */
    var CourseUpdateCollection = Backbone.Collection.extend({
        // instantiator must set url

        model: CourseUpdateModel
    });
    return CourseUpdateCollection;
});
