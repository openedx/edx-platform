define(['backbone', 'underscore'], function(Backbone, _) {
    var AssignmentGrade = Backbone.Model.extend({
        defaults: {
            graderType: null, // the type label (string). May be "notgraded" which implies None.
            locator: null // locator for the block
        },
        idAttribute: 'locator',
        urlRoot: '/xblock/',
        url: function() {
            // add ?fields=graderType to the request url (only needed for fetch, but innocuous for others)
            return Backbone.Model.prototype.url.apply(this) + '?' + $.param({fields: 'graderType'});
        }
    });
    return AssignmentGrade;
});
