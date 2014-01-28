define(["backbone", "js/models/syllabus"],
        function(Backbone, SyllabusModel) {
    var SyllabusCollection = Backbone.Collection.extend({
        model: SyllabusModel,
        url: function() { return CMS.URL.SYLLABUS; },
    });
    return SyllabusCollection;
});
