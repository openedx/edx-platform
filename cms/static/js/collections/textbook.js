// eslint-disable-next-line no-undef
define(['backbone', 'js/models/textbook'],
    function(Backbone, TextbookModel) {
        var TextbookCollection = Backbone.Collection.extend({
            model: TextbookModel,
            // eslint-disable-next-line no-undef
            url: function() { return CMS.URL.TEXTBOOKS; }
        });
        return TextbookCollection;
    });
