define([
    'gettext', 'js/models/section', 'js/collections/textbook', 'js/views/list_textbooks'
], function(gettext, Section, TextbookCollection, ListTextbooksView) {
    'use strict';
    return function(textbooksJson) {
        var textbooks = new TextbookCollection(textbooksJson, {parse: true}),
            tbView = new ListTextbooksView({collection: textbooks});

        $('.content-primary').append(tbView.render().el);
        $('.nav-actions .new-button').click(function(event) {
            tbView.addOne(event);
        });
        $(window).on('beforeunload', function() {
            var dirty = textbooks.find(function(textbook) { return textbook.isDirty(); });
            if (dirty) {
                return gettext('You have unsaved changes. Do you really want to leave this page?');
            }
        });
    };
});
