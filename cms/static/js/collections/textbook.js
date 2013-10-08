define(["backbone", "js/models/textbook"],
        function(Backbone, TextbookModel) {
    var TextbookCollection = Backbone.Collection.extend({
        model: TextbookModel,
        url: function() { return CMS.URL.TEXTBOOKS; },
        save: function(options) {
            return this.sync('update', this, options);
        }
    });
    return TextbookCollection;
});
