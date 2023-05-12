// eslint-disable-next-line no-undef
define(['backbone', 'jquery', 'jquery.ui'], function(Backbone, $) {
    // course update -- biggest kludge here is the lack of a real id to map updates to originals
    // eslint-disable-next-line no-var
    var CourseUpdate = Backbone.Model.extend({
        defaults: {
            date: $.datepicker.formatDate('MM d, yy', new Date()),
            content: ''
        },
        // eslint-disable-next-line consistent-return
        validate: function(attrs) {
            /* eslint-disable-next-line camelcase, no-var */
            var date_exists = (attrs.date !== null && attrs.date !== '');
            /* eslint-disable-next-line camelcase, no-var */
            var date_is_valid_string = ($.datepicker.formatDate('MM d, yy', new Date(attrs.date)) === attrs.date);
            // eslint-disable-next-line camelcase
            if (!(date_exists && date_is_valid_string)) {
                return {date_required: gettext('Action required: Enter a valid date.')};
            }
        }
    });
    return CourseUpdate;
}); // end define()
