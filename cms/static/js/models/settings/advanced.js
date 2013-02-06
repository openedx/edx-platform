if (!CMS.Models['Settings']) CMS.Models.Settings = {};

CMS.Models.Settings.Advanced = Backbone.Model.extend({
    defaults: {
        // the properties are whatever the user types in (in addition to whatever comes originally from the server)
    },
    // which keys to send as the deleted keys on next save
    deleteKeys : [],
    blacklistKeys : [], // an array which the controller should populate directly for now [static not instance based]

    validate: function (attrs) {
        var errors = {};
        for (var key in attrs) {
            if (_.contains(this.blacklistKeys, key)) {
                errors[key] = key + " is a reserved keyword or has another editor";
            }
        }
        if (!_.isEmpty(errors)) return errors;
    }
});
