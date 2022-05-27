define(['backbone', 'jquery', 'jquery.ui'], function(Backbone, $) {
    // course update -- biggest kludge here is the lack of a real id to map updates to originals
    var CourseUpdate = Backbone.Model.extend({
        defaults: {
            date: $.datepicker.formatDate('MM d, yy', new Date()),
            content: ''
        },
        validate: function(attrs) {
            var date_exists = (attrs.date !== null && attrs.date !== '');
            var date_is_valid_string = ($.datepicker.formatDate('MM d, yy', new Date(attrs.date)) === attrs.date);
            if (!(date_exists && date_is_valid_string)) {
                return {date_required: gettext('Action required: Enter a valid date.')};
            }
        }
    });
    return CourseUpdate;
}); // end define()
