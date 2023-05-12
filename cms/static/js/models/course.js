define(['backbone'], function(Backbone) {
    var Course = Backbone.Model.extend({
        defaults: {
            name: ''
        },
        // eslint-disable-next-line consistent-return
        validate: function(attrs, options) {
            if (!attrs.name) {
                return gettext('You must specify a name');
            }
        }
    });
    return Course;
});
