define(["backbone", "js/models/syllabus"],
        function(Backbone, SyllabusModel) {
    var SyllabusCollection = Backbone.Collection.extend({
        model: SyllabusModel,
        url: function() { return CMS.URL.SYLLABUS; },
        save: function(options) {
            return this.sync('update', this, options);
        }
    });
    return SyllabusCollection;
});
