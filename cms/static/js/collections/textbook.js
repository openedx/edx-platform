define(["backbone", "js/models/textbook"],
        function(Backbone, TextbookModel) {
    var TextbookCollection = Backbone.Collection.extend({
        model: TextbookModel,
        url: function() { return CMS.URL.TEXTBOOKS; }
    });
    return TextbookCollection;
});
